import logging
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from db.models.playlist import Playlist
from db.models.sync_session import SyncProvider, SyncSession, SyncStatus, TrackListKind
from db.playlist import _get_playlist_by_id
from db.session import SessionDep, get_isolated_session
from db.sync_session import _build_tracks, _create_sync_session, _update_sync_session
from lib.common import ExternalPlaylist, Song
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
from lib.track import _find_track
from lib.utils import _convert_seconds_to_readable_time, _get_now

BASE_DIR = Path(__file__).resolve().parent.parent
SPOTAPI_DIR = BASE_DIR / "SpotAPI"

if SPOTAPI_DIR.exists():
    sys.path.insert(0, str(SPOTAPI_DIR))
else:
    raise RuntimeError(
        f"SpotAPI submodule not found at {SPOTAPI_DIR}. Did you run `git submodule update --init --recursive`?"
    )

from spotapi.album import PublicAlbum
from spotapi.playlist import PublicPlaylist

logger = logging.getLogger(__name__)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")


def _get_spotify_playlist(playlist_id: str) -> ExternalPlaylist:
    playlist = PublicPlaylist(playlist_id)
    playlist_info = playlist.get_playlist_info()

    thumbnail_metadata = max(
        playlist_info["data"]["playlistV2"]["ownerV2"]["data"]["avatar"]["sources"],
        key=lambda x: x.get("height"),
    )

    return ExternalPlaylist(
        id=playlist_id,
        name=playlist.get_playlist_info()["data"]["playlistV2"]["name"],
        total=playlist.get_playlist_info()["data"]["playlistV2"]["content"][
            "totalCount"
        ],
        thumbnail_url=thumbnail_metadata.get("url"),
    )


def _get_spotify_playlist_songs(playlist_id: str) -> list[Song]:
    offset = 0
    limit = 50
    songs: list[Song] = []

    playlist = PublicPlaylist(playlist_id)
    playlist_info = playlist.get_playlist_info(limit=limit)

    while offset < playlist_info["data"]["playlistV2"]["content"]["totalCount"]:
        for item in playlist_info["data"]["playlistV2"]["content"]["items"]:
            album_metadata = item["itemV3"]["data"]["identityTrait"][
                "contentHierarchyParent"
            ]
            song = Song(
                artist_name=item["itemV2"]["data"]["albumOfTrack"]["artists"]["items"][
                    0
                ]["profile"]["name"],
                year=album_metadata["publishingMetadataTrait"]["firstPublishedAt"][
                    "isoString"
                ][:4],
                track_name=item["itemV2"]["data"]["name"],
                duration=item["itemV3"]["data"]["consumptionExperienceTrait"][
                    "duration"
                ]["seconds"],
                album_name=album_metadata["identityTrait"]["name"],
            )
            songs.append(song)
        offset += limit
        playlist_info = playlist.get_playlist_info(offset=offset, limit=limit)
        logger.info(f"Fetched {len(songs)} songs...")
    logger.info(f"Total songs fetched from Spotify playlist: {len(songs)}")

    return songs


def _sync_spotify_playlist_task(
    playlist: Playlist,
    sync_session: SyncSession,
) -> None:
    """Sync a Spotify playlist to Jellyfin."""
    with get_isolated_session() as session:
        playlist_id = playlist.playlist_id
        username = playlist.username
        started_at = sync_session.started_at

        try:
            spotify_playlist = _get_spotify_playlist(playlist_id=playlist_id)
            spotify_playlist_name = spotify_playlist.name
            songs = _get_spotify_playlist_songs(playlist_id=playlist_id)
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
                formatted_track_name = f"{song.artist_name} - {song.album_name}: {song.track_name} ({song.year})"

                track_names.append(formatted_track_name)

                track = _find_track(
                    artist_name=song.artist_name,
                    track_name=song.track_name,
                    album_name=song.album_name,
                    year=song.year,
                    duration=song.duration,
                )

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
            sync_session = _update_sync_session(
                session=session, sync_session=sync_session
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
                        status_code=500,
                        detail="Unable to create new playlist in Jellyfin",
                    )

            sync_session.target_playlist_id = existing_playlist_id
            sync_session.target_playlist_name = spotify_playlist_name
            sync_session = _update_sync_session(
                session=session, sync_session=sync_session
            )

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
                    duration_seconds=int(
                        finished_at.timestamp() - started_at.timestamp()
                    ),
                    status=SyncStatus.completed,
                )
                sync_session.tracks = _build_tracks(
                    sync_session_id=sync_session.id,
                    names=track_names,
                    kind=TrackListKind.total,
                )
                _create_sync_session(session=session, sync_session=sync_session)
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

            spotify_playlist_thumbnail_url = spotify_playlist.thumbnail_url
            _update_jellyfin_playlist_image(
                playlist_id=playlist_id,
                image_url=spotify_playlist_thumbnail_url
                if spotify_playlist_thumbnail_url.endswith((".png", "jpg", "jpeg"))
                else None,
            )

            finished_at = _get_now()
            duration_taken = finished_at.timestamp() - started_at.timestamp()

            if len(DISCORD_WEBHOOK_URL) > 0:
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

            sync_session = _update_sync_session(
                session=session, sync_session=sync_session
            )
        except Exception as e:
            finished_at = _get_now()
            sync_session.status = SyncStatus.failed
            sync_session.finished_at = finished_at
            sync_session.duration_seconds = int(
                finished_at.timestamp() - started_at.timestamp()
            )
            sync_session.error_message = str(e)
            sync_session.target_playlist_name = playlist.playlist_name
            sync_session = _update_sync_session(
                session=session, sync_session=sync_session
            )


def _sync_spotify_playlist(
    item: Playlist,
    session: SessionDep,
) -> dict[str, str]:
    """Sync a Spotify playlist to Jellyfin."""
    playlist = _get_playlist_by_id(session=session, playlist_id=item.id)

    if not playlist:
        raise HTTPException(
            status_code=404, detail=f"Unable to find playlist: {item.playlist_id}"
        )

    playlist_id = playlist.playlist_id
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
    session.expunge(sync_session)
    _sync_spotify_playlist_task(playlist=playlist, sync_session=sync_session)
    return {"id": str(sync_session.id)}
