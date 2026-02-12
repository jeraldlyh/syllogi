import logging
import os
import time
from typing import Annotated, Any, Mapping
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel

from db.notification import _get_notifications
from db.import_session import _create_import_session, _build_tracks
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
from lib.utils import _convert_seconds_to_readable_time
from db.models.notification import NotificationChannel
from db.models.import_session import ImportProvider, ImportSession, TrackListKind

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


@router.post("/import")
async def import_playlist(item: ImportPlaylist, session: SessionDep):
    playlist_id = item.playlist_id
    username = item.username

    start = time.time()
    spotify_playlist = _get_playlist(playlist_id=playlist_id)
    songs = _get_songs_by_playlist(playlist_id=playlist_id)
    user = _get_jellyfin_user_by_name(username=username)

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

    spotify_playlist_name = spotify_playlist["data"]["playlistV2"]["name"]
    jellyfin_user_id = user.get("Id")

    if not jellyfin_user_id:
        raise HTTPException(
            status_code=400, detail=f"Unable to find user ID from {username}"
        )
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
            status_code=500, detail="Unable to determine existing playlist ID"
        )

    if len(jellyfin_tracks) == 0:
        end = time.time()
        import_session = ImportSession(
            provider=ImportProvider.spotify,
            provider_playlist_id=playlist_id,
            provider_playlist_name=spotify_playlist_name,
            target_user_id=jellyfin_user_id,
            target_username=username,
            target_playlist_id=existing_playlist_id,
            target_playlist_name=spotify_playlist_name,
            started_at=datetime.fromtimestamp(start, tz=timezone.utc),
            finished_at=datetime.fromtimestamp(end, tz=timezone.utc),
            duration_seconds=int(end - start),
            success=False,
        )
        import_session.tracks = _build_tracks(
            import_session_id=import_session.id,
            names=track_names,
            kind=TrackListKind.total,
        )
        _create_import_session(session=session, import_session=import_session)
        return

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
        spotify_playlist["data"]["playlistV2"]["ownerV2"]["data"]["avatar"]["sources"],
        key=lambda x: x.get("height"),
    )
    spotify_playlist_thumbnail_url = spotify_playlist_thumbnail_metadata.get("url")
    _update_jellyfin_playlist_image(
        playlist_id=playlist_id,
        image_url=spotify_playlist_thumbnail_url
        if spotify_playlist_thumbnail_url.endswith((".png", "jpg", "jpeg"))
        else None,
    )
    end = time.time()

    notifications = _get_notifications(session=session)

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
                        "value": _convert_seconds_to_readable_time(seconds=end - start),
                        "inline": True,
                    },
                ],
                timestamp=True,
            )
    import_session = ImportSession(
        provider=ImportProvider.spotify,
        provider_playlist_id=playlist_id,
        provider_playlist_name=spotify_playlist_name,
        target_user_id=jellyfin_user_id,
        target_username=username,
        target_playlist_id=existing_playlist_id,
        target_playlist_name=spotify_playlist_name,
        started_at=datetime.fromtimestamp(start, tz=timezone.utc),
        finished_at=datetime.fromtimestamp(end, tz=timezone.utc),
        duration_seconds=int(end - start),
        success=True,
    )

    new_track_names = [track["track"]["name"] for track in new_tracks]
    outdated_track_names = [track["Name"] for track in outdated_tracks]

    import_session.tracks = (
        _build_tracks(
            import_session_id=import_session.id,
            names=track_names,
            kind=TrackListKind.total,
        )
        + _build_tracks(
            import_session_id=import_session.id,
            names=missing_track_names,
            kind=TrackListKind.missing,
        )
        + _build_tracks(
            import_session_id=import_session.id,
            names=new_track_names,
            kind=TrackListKind.new,
        )
        + _build_tracks(
            import_session_id=import_session.id,
            names=outdated_track_names,
            kind=TrackListKind.outdated,
        )
    )

    _create_import_session(session=session, import_session=import_session)

    return jellyfin_tracks
