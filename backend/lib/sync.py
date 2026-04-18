import logging
import os
import time

from fastapi import HTTPException, status

from db.models.playlist import Playlist, PlaylistProvider
from db.models.sync_session import SyncProvider, SyncSession, SyncStatus, TrackListKind
from db.playlist import get_playlist_by_id
from db.session import SessionDep, get_isolated_session
from db.sync_session import build_tracks, create_sync_session, update_sync_session
from lib.common import ExternalPlaylist, PlaylistDiff, ResolvedTrack, Track
from lib.download import download_missing_tracks
from lib.jellyfin import (
    add_songs_to_jellyfin_playlist,
    create_jellyfin_playlist,
    delete_songs_from_jellyfin_playlist,
    get_jellyfin_playlist_songs,
    get_jellyfin_playlists,
    get_jellyfin_user_by_name,
    rescan_jellyfin_library,
    update_jellyfin_playlist_image,
)
from lib.notification import send_discord_notification
from lib.spotify import get_spotify_playlist, get_spotify_playlist_songs
from lib.track import _find_track
from lib.utils import convert_seconds_to_readable_time, get_now
from lib.youtube import _get_youtube_playlist, _get_youtube_playlist_songs

logger = logging.getLogger(__name__)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")


def _resolve_songs(
    songs: list[Track],
) -> tuple[list[ResolvedTrack], list[ResolvedTrack]]:
    """Verifies which tracks from the source playlist can be found in the Jellyfin library.

    Returns (found_tracks, missing_tracks).
    """
    found: list[ResolvedTrack] = []
    missing: list[ResolvedTrack] = []

    for song in songs:
        display_name = f"{song.artist_name} - {song.album_name}: {song.track_name}"
        track = _find_track(
            artist_name=song.artist_name,
            track_name=song.track_name,
            album_name=song.album_name,
            year=song.year,
            duration=song.duration,
        )

        jellyfin_id = track.get("track", {}).get("id")

        resolved = ResolvedTrack(
            track=song,
            jellyfin_id=jellyfin_id,
            display_name=display_name,
        )

        if resolved.jellyfin_id is not None:
            logger.info(f"{display_name}: OK")
            found.append(resolved)
        else:
            logger.warning(f"{display_name}: MISSING")
            missing.append(resolved)

    return found, missing


def _diff_tracks(
    resolved_tracks: list[ResolvedTrack],
    existing_tracks: list[dict],
) -> PlaylistDiff:
    """Compute the difference between the source playlist (resolved_tracks) and the existing Jellyfin playlist (existing_tracks).

    - added:     tracks in source that are NOT in the existing playlist
    - removed:   tracks in the existing playlist that are NOT in the source
    - unchanged: tracks present in both
    """
    existing_ids: set[str] = {track["Id"] for track in existing_tracks}
    source_ids: set[str] = {
        track.jellyfin_id for track in resolved_tracks if track.jellyfin_id is not None
    }

    diff = PlaylistDiff()

    for track in resolved_tracks:
        if track.jellyfin_id is None:
            continue

        if track.jellyfin_id in existing_ids:
            diff.unchanged.append(track)
        else:
            diff.added.append(track)

    for track in existing_tracks:
        if track["Id"] not in source_ids:
            diff.removed.append(track)

    return diff


async def _sync_playlist_task(
    internal_playlist: Playlist,
    external_playlist: ExternalPlaylist,
    songs: list[Track],
    sync_session: SyncSession,
) -> None:
    """Sync a playlist (Spotify/Youtube) to Jellyfin in a background task."""
    with get_isolated_session() as session:
        playlist_id = internal_playlist.playlist_id
        username = internal_playlist.username
        started_at = sync_session.started_at
        external_playlist_name = external_playlist.name

        try:
            user = get_jellyfin_user_by_name(username=username)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unable to find username: {username}",
                )

            jellyfin_user_id = user.get("Id")
            if not jellyfin_user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unable to find user ID from {username}",
                )

            found_tracks, missing_tracks = _resolve_songs(songs)

            track_names = [
                f"{song.artist_name} - {song.album_name}: {song.track_name}"
                for song in songs
            ]

            sync_session.provider_playlist_name = external_playlist_name
            sync_session.target_user_id = jellyfin_user_id
            sync_session = update_sync_session(
                session=session, sync_session=sync_session
            )

            internal_playlist_name = internal_playlist.playlist_name
            jellyfin_playlists = get_jellyfin_playlists(user_id=jellyfin_user_id)
            existing_playlist = next(
                (
                    playlist
                    for playlist in jellyfin_playlists
                    if internal_playlist_name == playlist.get("Name")
                ),
                {},
            )

            existing_playlist_id = existing_playlist.get("Id")

            if not existing_playlist_id:
                new_playlist = create_jellyfin_playlist(
                    playlist_name=internal_playlist_name, user_id=jellyfin_user_id
                )
                existing_playlist_id = new_playlist.get("Id")
                if not existing_playlist_id:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Unable to create new playlist in Jellyfin",
                    )

            sync_session.target_playlist_id = existing_playlist_id
            sync_session.target_playlist_name = internal_playlist.playlist_name
            sync_session = update_sync_session(
                session=session, sync_session=sync_session
            )

            downloaded_tracks: list[Track] = []

            if missing_tracks and internal_playlist.enable_download:
                missing_songs = [missing.track for missing in missing_tracks]
                (
                    newly_downloaded_tracks,
                    still_missing_tracks,
                ) = await download_missing_tracks(missing_tracks=missing_songs)
                downloaded_tracks = newly_downloaded_tracks

                if len(downloaded_tracks) > 0:
                    logger.info(
                        f"Downloaded {len(downloaded_tracks)} missing songs via yt-dlp"
                    )

                    rescan_jellyfin_library()

                    # NOTE: This requires a full library scan which takes a long time depending on the size of library.
                    # while is_jellyfin_scanning_library():
                    #     logger.info(
                    #         "Waiting for Jellyfin to finish scanning library..."
                    #     )
                    #     time.sleep(15)
                    time.sleep(15)

                    newly_found_tracks, still_missing_tracks_after_download = (
                        _resolve_songs(downloaded_tracks)
                    )
                    found_tracks.extend(newly_found_tracks)

                    missing_tracks = [
                        ResolvedTrack(
                            track=track,
                            display_name=f"{track.artist_name} - {track.album_name}: {track.track_name}",
                        )
                        for track in still_missing_tracks
                    ] + still_missing_tracks_after_download

            existing_jellyfin_tracks = get_jellyfin_playlist_songs(
                playlist_id=existing_playlist_id, user_id=jellyfin_user_id
            )

            diff = _diff_tracks(
                resolved_tracks=found_tracks,
                existing_tracks=existing_jellyfin_tracks,
            )

            num_of_added_tracks = len(diff.added)
            num_of_removed_tracks = len(diff.removed)
            num_of_missing_tracks = len(missing_tracks)
            num_of_downloaded_tracks = len(downloaded_tracks)

            if num_of_removed_tracks > 0:
                logger.info(
                    f"Removing {num_of_removed_tracks} outdated songs from "
                    f"{internal_playlist.playlist_name} playlist"
                )
                removed_entry_ids = [track["Id"] for track in diff.removed]
                delete_songs_from_jellyfin_playlist(
                    playlist_id=existing_playlist_id, track_ids=removed_entry_ids
                )

            if num_of_added_tracks > 0:
                logger.info(
                    f"Adding {num_of_added_tracks} new songs to "
                    f"{internal_playlist.playlist_name} playlist"
                )
                added_track_ids = [
                    track.jellyfin_id
                    for track in diff.added
                    if track.jellyfin_id is not None
                ]
                add_songs_to_jellyfin_playlist(
                    playlist_id=existing_playlist_id,
                    user_id=jellyfin_user_id,
                    track_ids=added_track_ids,
                )

            spotify_playlist_thumbnail_url = external_playlist.thumbnail_url
            update_jellyfin_playlist_image(
                playlist_id=playlist_id,
                image_url=spotify_playlist_thumbnail_url
                if spotify_playlist_thumbnail_url.endswith((".png", "jpg", "jpeg"))
                else None,
            )

            finished_at = get_now()
            duration_taken = finished_at.timestamp() - started_at.timestamp()

            if len(DISCORD_WEBHOOK_URL) > 0:
                send_discord_notification(
                    DISCORD_WEBHOOK_URL,
                    title="Import Summary",
                    fields=[
                        {"name": "Username", "value": username, "inline": True},
                        {
                            "name": "Playlist",
                            "value": external_playlist_name,
                            "inline": True,
                        },
                        {
                            "name": "Tracks",
                            "value": f"{num_of_added_tracks} 🔺 {num_of_removed_tracks} 🔻 {num_of_downloaded_tracks} 💾",
                            "inline": True,
                        },
                        {
                            "name": "Missing",
                            "value": num_of_missing_tracks,
                            "inline": True,
                        },
                        {
                            "name": "Total",
                            "value": len(songs),
                            "inline": True,
                        },
                        {
                            "name": "Time Taken",
                            "value": convert_seconds_to_readable_time(
                                seconds=duration_taken
                            ),
                            "inline": True,
                        },
                    ],
                    timestamp=True,
                )

            added_track_names = [track.display_name for track in diff.added]
            removed_track_names = [
                jellyfin_track.get("Name", "") for jellyfin_track in diff.removed
            ]
            missing_track_names = [track.display_name for track in missing_tracks]
            downloaded_track_names = [
                f"{track.artist_name} - {track.album_name}: {track.track_name}"
                for track in downloaded_tracks
            ]

            sync_session.finished_at = finished_at
            sync_session.duration_seconds = int(duration_taken)
            sync_session.status = SyncStatus.completed
            sync_session.tracks = (
                build_tracks(
                    sync_session_id=sync_session.id,
                    names=track_names,
                    kind=TrackListKind.total,
                )
                + build_tracks(
                    sync_session_id=sync_session.id,
                    names=missing_track_names,
                    kind=TrackListKind.missing,
                )
                + build_tracks(
                    sync_session_id=sync_session.id,
                    names=added_track_names,
                    kind=TrackListKind.new,
                )
                + build_tracks(
                    sync_session_id=sync_session.id,
                    names=removed_track_names,
                    kind=TrackListKind.outdated,
                )
                + build_tracks(
                    sync_session_id=sync_session.id,
                    names=downloaded_track_names,
                    kind=TrackListKind.downloaded,
                )
            )

            sync_session = update_sync_session(
                session=session, sync_session=sync_session
            )
        except Exception as e:
            finished_at = get_now()
            sync_session.status = SyncStatus.failed
            sync_session.finished_at = finished_at
            sync_session.duration_seconds = int(
                finished_at.timestamp() - started_at.timestamp()
            )
            sync_session.error_message = str(e)
            sync_session.target_playlist_name = internal_playlist.playlist_name
            sync_session = update_sync_session(
                session=session, sync_session=sync_session
            )


async def _sync_playlist(playlist: Playlist, session: SessionDep) -> dict[str, str]:
    """Sync a playlist (Spotify/Youtube) to Jellyfin."""
    internal_playlist = get_playlist_by_id(session=session, playlist_id=playlist.id)

    if not internal_playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unable to find playlist: {playlist.playlist_id}",
        )

    playlist_id = playlist.playlist_id
    username = playlist.username
    started_at = get_now()

    sync_session = SyncSession(
        provider=SyncProvider(internal_playlist.provider.value),
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
    create_sync_session(session=session, sync_session=sync_session)
    session.expunge(sync_session)

    songs: list[Track] = []
    external_playlist: ExternalPlaylist | None = None

    match internal_playlist.provider:
        case PlaylistProvider.spotify:
            songs = get_spotify_playlist_songs(playlist_id=playlist_id)
            external_playlist = get_spotify_playlist(playlist_id=playlist_id)
        case PlaylistProvider.youtube:
            songs = _get_youtube_playlist_songs(playlist_id=playlist_id)
            external_playlist = _get_youtube_playlist(playlist_id=playlist_id)

    await _sync_playlist_task(
        internal_playlist=internal_playlist,
        external_playlist=external_playlist,
        songs=songs,
        sync_session=sync_session,
    )
    return {"id": str(sync_session.id)}
