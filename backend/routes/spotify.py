import logging
import os
from typing import Annotated, Any, Mapping

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel

from db.sync_session import _build_tracks, _create_sync_session, _update_sync_session
from db.models.sync_session import SyncProvider, SyncSession, SyncStatus, TrackListKind
from db.models.notification import NotificationChannel
from db.notification import _get_notifications
from db.session import SessionDep
from lib.jellyfin import (
    _add_songs_to_jellyfin_playlist,
    _create_jellyfin_playlist,
    _delete_songs_from_jellyfin_playlist,
    _get_jellyfin_playlist_songs,
    _get_jellyfin_playlists,
    _get_jellyfin_user_by_name,
    _update_jellyfin_playlist_image,
)
from lib.notification import _send_discord_notification
from lib.spotify import _get_playlist, _get_songs_by_playlist
from lib.track import _find_track
from lib.utils import _convert_seconds_to_readable_time, _get_now

router = APIRouter()
logger = logging.getLogger(__name__)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")


class ImportPlaylist(BaseModel):
    playlist_id: str
    username: str


@router.get("/{id}")
async def get_playlist(
    id: Annotated[str, Path(min_length=1, description="Spotify Playlist ID")],
) -> Mapping[str, Any]:
    return _get_playlist(id)


@router.post("")
def import_playlist(item: ImportPlaylist, session: SessionDep) -> dict[str, str]:
    playlist_id = item.playlist_id
    username = item.username

    started_at = _get_now()

    sync_session = SyncSession(
        provider=SyncProvider.spotify,
        provider_playlist_id=playlist_id,
        provider_playlist_name="",
        target_user_id="",
        target_username=username,
        target_playlist_id="",
        target_playlist_name="",
        started_at=started_at,
        finished_at=started_at,
        duration_seconds=0,
        status=SyncStatus.pending,
    )
    _create_sync_session(session=session, sync_session=sync_session)

    try:
        spotify_playlist = _get_playlist(playlist_id=playlist_id)
        spotify_playlist_name = spotify_playlist["data"]["playlistV2"]["name"]
        songs = _get_songs_by_playlist(playlist_id=playlist_id)
        user = _get_jellyfin_user_by_name(username=username)

        jellyfin_user_id = user.get("Id")
        if not user:
            raise HTTPException(
                status_code=400, detail=f"Unable to find username: {username}"
            )

        jellyfin_tracks: list[dict] = []
        missing_track_names: list[str] = []
        track_names: list[str] = []
        for song in songs:
            artist_name = song["itemV2"]["data"]["albumOfTrack"]["artists"]["items"][0][
                "profile"
            ]["name"]
            album_song_name = song["itemV2"]["data"]["albumOfTrack"]["name"]
            formatted_track_name = f"{artist_name} - {album_song_name}"

            track_names.append(formatted_track_name)

            track = _find_track(artist_name=artist_name, track_name=album_song_name)
            if not track.get("track", {}).get("id"):
                logger.info(f"{formatted_track_name} - {album_song_name}: RETRYING")
                album_song_name = song["itemV2"]["data"]["name"]
                track = _find_track(artist_name=artist_name, track_name=album_song_name)

            if track.get("track", {}).get("id") is not None:
                logger.info(f"{formatted_track_name}: OK")
                jellyfin_tracks.append(track)
            else:
                missing_track_names.append(formatted_track_name)
                logger.warning(f"{formatted_track_name}: MISSING")

        if not jellyfin_user_id:
            raise HTTPException(
                status_code=400, detail=f"Unable to find user ID from {username}"
            )

        sync_session.provider_playlist_name = spotify_playlist_name
        sync_session.target_user_id = jellyfin_user_id
        _update_sync_session(session=session, sync_session=sync_session)

        jellyfin_playlists = _get_jellyfin_playlists(user_id=jellyfin_user_id)
        existing_playlist = next(
            (
                playlist
                for playlist in jellyfin_playlists
                if spotify_playlist_name == playlist.get("Name")
            ),
            {},
        )

        existing_playlist_id = existing_playlist.get("Id")

        if not existing_playlist_id:
            new_playlist = _create_jellyfin_playlist(
                playlist_name=spotify_playlist_name, user_id=jellyfin_user_id
            )
            existing_playlist_id = new_playlist.get("Id")

            if not existing_playlist_id:
                raise HTTPException(
                    status_code=500, detail="Unable to create new playlist in Jellyfin"
                )

        sync_session.target_playlist_id = existing_playlist_id
        sync_session.target_playlist_name = spotify_playlist_name
        _update_sync_session(session=session, sync_session=sync_session)

        if len(jellyfin_tracks) == 0:
            finished_at = _get_now()
            sync_session = SyncSession(
                provider=SyncProvider.spotify,
                provider_playlist_id=playlist_id,
                provider_playlist_name=spotify_playlist_name,
                target_user_id=jellyfin_user_id,
                target_username=username,
                target_playlist_id=existing_playlist_id,
                target_playlist_name=spotify_playlist_name,
                started_at=started_at,
                finished_at=finished_at,
                duration_seconds=int(finished_at.timestamp() - started_at.timestamp()),
                status=SyncStatus.completed,
            )
            sync_session.tracks = _build_tracks(
                sync_session_id=sync_session.id,
                names=track_names,
                kind=TrackListKind.total,
            )
            _create_sync_session(session=session, sync_session=sync_session)
            return {"id": str(sync_session.id)}

        existing_tracks = _get_jellyfin_playlist_songs(
            playlist_id=existing_playlist_id, user_id=jellyfin_user_id
        )

        new_tracks: list[dict] = []
        outdated_tracks: list[dict] = []

        for jellyfin_track in jellyfin_tracks:
            jellyfin_track_id = jellyfin_track["track"]["id"]

            existing_track = any(
                jellyfin_track_id == existing_track["Id"]
                for existing_track in existing_tracks
            )

            if not existing_track:
                new_tracks.append(jellyfin_track)

        for existing_track in existing_tracks:
            existing_track_id = existing_track["Id"]

            existing_jellyfin_track = any(
                existing_track_id == jellyfin_track["track"]["id"]
                for jellyfin_track in jellyfin_tracks
            )

            if not existing_jellyfin_track:
                outdated_tracks.append(existing_track)

        num_of_new_tracks = len(new_tracks)
        num_of_outdated_tracks = len(outdated_tracks)
        num_of_missing_tracks = len(missing_track_names)

        if num_of_new_tracks > 0:
            logger.info(
                f"Adding {num_of_new_tracks} songs to {spotify_playlist_name} playlist"
            )
            new_track_ids = [track["track"]["id"] for track in jellyfin_tracks]
            _add_songs_to_jellyfin_playlist(
                playlist_id=existing_playlist_id,
                user_id=jellyfin_user_id,
                track_ids=new_track_ids,
            )

        if num_of_outdated_tracks > 0:
            logger.info(
                f"Deleting {num_of_outdated_tracks} songs from {spotify_playlist_name} playlist"
            )
            outdated_track_ids = [track["Id"] for track in existing_tracks]
            _delete_songs_from_jellyfin_playlist(
                playlist_id=existing_playlist_id, track_ids=outdated_track_ids
            )

        spotify_playlist_thumbnail_metadata = max(
            spotify_playlist["data"]["playlistV2"]["ownerV2"]["data"]["avatar"][
                "sources"
            ],
            key=lambda x: x.get("height"),
        )
        spotify_playlist_thumbnail_url = spotify_playlist_thumbnail_metadata.get("url")
        _update_jellyfin_playlist_image(
            playlist_id=playlist_id,
            image_url=spotify_playlist_thumbnail_url
            if spotify_playlist_thumbnail_url.endswith((".png", "jpg", "jpeg"))
            else None,
        )

        finished_at = _get_now()
        notifications = _get_notifications(session=session)
        duration_taken = finished_at.timestamp() - started_at.timestamp()

        for notification in notifications:
            if notification.channel == NotificationChannel.discord:
                _send_discord_notification(
                    DISCORD_WEBHOOK_URL,
                    title="Import Summary",
                    fields=[
                        {"name": "Username", "value": username, "inline": True},
                        {
                            "name": "Playlist",
                            "value": spotify_playlist_name,
                            "inline": True,
                        },
                        {
                            "name": "New/Outdated Tracks(s)",
                            "value": f"{num_of_new_tracks} 🔺 {num_of_outdated_tracks} 🔻",
                            "inline": True,
                        },
                        {
                            "name": "Missing Tracks(s)",
                            "value": num_of_missing_tracks,
                            "inline": True,
                        },
                        {
                            "name": "Total Tracks(s)",
                            "value": len(songs),
                            "inline": True,
                        },
                        {
                            "name": "Time Taken",
                            "value": _convert_seconds_to_readable_time(
                                seconds=duration_taken
                            ),
                            "inline": True,
                        },
                    ],
                    timestamp=True,
                )

        new_track_names = [track["track"]["name"] for track in new_tracks]
        outdated_track_names = [track["Name"] for track in outdated_tracks]

        sync_session.finished_at = finished_at
        sync_session.duration_seconds = int(duration_taken)
        sync_session.status = SyncStatus.completed
        sync_session.tracks = (
            _build_tracks(
                sync_session_id=sync_session.id,
                names=track_names,
                kind=TrackListKind.total,
            )
            + _build_tracks(
                sync_session_id=sync_session.id,
                names=missing_track_names,
                kind=TrackListKind.missing,
            )
            + _build_tracks(
                sync_session_id=sync_session.id,
                names=new_track_names,
                kind=TrackListKind.new,
            )
            + _build_tracks(
                sync_session_id=sync_session.id,
                names=outdated_track_names,
                kind=TrackListKind.outdated,
            )
        )

        _update_sync_session(session=session, sync_session=sync_session)
        return {"id": str(sync_session.id)}
    except Exception as e:
        finished_at = _get_now()
        sync_session.status = SyncStatus.failed
        sync_session.finished_at = finished_at
        sync_session.duration_seconds = int(
            finished_at.timestamp() - started_at.timestamp()
        )
        sync_session.error_message = str(e)
        _update_sync_session(session=session, sync_session=sync_session)
        return {"id": str(sync_session.id)}
