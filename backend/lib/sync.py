import asyncio
import logging
import uuid

from fastapi import HTTPException, status

from db.models.sync import (
    Sync,
    SyncProvider,
    SyncSession,
    SyncSessionTrackType,
    SyncStatus,
)
from db.sync import get_sync_by_id
from db.session import get_isolated_session
from db.sync_session import (
    build_sync_session_tracks,
    create_sync_session,
    get_sync_session_by_id,
    update_sync_session,
)
from lib.download import download_missing_tracks
from lib.env import get_environment_variable
from lib.models.common import (
    ExternalSync,
    ExternalTrack,
    SyncDiff,
    ResolvedTrack,
)
from lib.models.provider import ProviderTrack
from lib.notification import send_discord_notification
from lib.providers.base import MusicPlaylistProvider
from lib.spotify import get_spotify_playlist, get_spotify_playlist_songs
from lib.track import reconcile_after_download, resolve_tracks
from lib.utils import convert_seconds_to_readable_time, get_now, truncate
from lib.youtube import get_youtube_playlist, get_youtube_playlist_songs

logger = logging.getLogger(__name__)


def _diff_tracks(
    resolved_tracks: list[ResolvedTrack],
    existing_tracks: list[ProviderTrack],
) -> SyncDiff:
    """Compute the difference between the source playlist (resolved_tracks) and the
    existing provider playlist (existing_tracks).

    - added:     tracks in source that are NOT in the existing playlist
    - removed:   tracks in the existing playlist that are NOT in the source
    - unchanged: tracks present in both
    """
    existing_ids: set[str] = {track.id for track in existing_tracks}
    source_ids: set[str] = {
        track.provider_track_id for track in resolved_tracks if track.provider_track_id
    }

    diff = SyncDiff()

    for track in resolved_tracks:
        if not track.provider_track_id:
            continue

        if track.provider_track_id in existing_ids:
            diff.unchanged.append(track)
        else:
            diff.added.append(track)

    for track in existing_tracks:
        if track.id not in source_ids:
            diff.removed.append(track)

    return diff


async def sync_playlist_task(
    provider: MusicPlaylistProvider,
    internal_playlist_id: str | uuid.UUID,
    external_playlist: ExternalSync,
    songs: list[ExternalTrack],
    sync_session_id: uuid.UUID,
) -> None:
    """Sync a playlist (Spotify/Youtube) to the music provider in a background task."""

    sync_session: SyncSession | None = None
    internal_sync: Sync | None = None

    with get_isolated_session() as session:
        try:
            internal_sync = get_sync_by_id(
                session=session, sync_id=internal_playlist_id
            )

            if not internal_sync:
                raise ValueError(
                    f"Unable to find sync config with ID: {internal_playlist_id}",
                )

            sync_session = get_sync_session_by_id(
                session=session, sync_session_id=sync_session_id
            )

            if not sync_session:
                raise ValueError(
                    f"Unable to find sync session with ID: {sync_session_id}",
                )

            username = internal_sync.username
            started_at = sync_session.started_at
            external_playlist_name = external_playlist.name

            found_tracks, missing_tracks = await resolve_tracks(provider, songs)

            track_names = [
                f"{song.artist_name} {song.album_name}: {song.track_name}"
                for song in songs
            ]

            internal_playlist_name = internal_sync.playlist_name
            (
                existing_playlist_id,
                provider_user_id,
            ) = await provider.get_or_create_playlist(
                playlist_name=internal_playlist_name,
                username=username,
                is_public=internal_sync.is_public,
            )

            sync_session.provider_playlist_name = external_playlist_name
            sync_session.target_user_id = provider_user_id
            sync_session.target_playlist_id = existing_playlist_id
            sync_session.target_playlist_name = internal_sync.playlist_name
            sync_session = update_sync_session(
                session=session, sync_session=sync_session
            )

            downloaded_tracks: list[ExternalTrack] = []

            if missing_tracks and internal_sync.enable_download:
                missing_songs = [missing.track for missing in missing_tracks]
                (
                    found_tracks_after_download,
                    missing_tracks_after_download,
                ) = await download_missing_tracks(missing_tracks=missing_songs)
                downloaded_tracks = found_tracks_after_download

                if len(downloaded_tracks) > 0:
                    logger.info(f"Downloaded {len(downloaded_tracks)} missing songs")

                    await provider.wait_for_rescan()

                    (
                        newly_found_tracks,
                        still_missing_tracks_after_download,
                    ) = await resolve_tracks(provider, tracks=downloaded_tracks)

                    found_tracks, missing_tracks = reconcile_after_download(
                        found_tracks=found_tracks,
                        missing_tracks=missing_tracks,
                        found_tracks_after_download=newly_found_tracks,
                        missing_tracks_after_download=missing_tracks_after_download,
                        missing_tracks_after_scan=still_missing_tracks_after_download,
                        get_key=lambda t: (t.track.artist_name, t.track.track_name),
                    )

            existing_provider_tracks = await provider.get_playlist_songs(
                playlist_id=existing_playlist_id, user_id=provider_user_id
            )

            diff = _diff_tracks(
                resolved_tracks=found_tracks,
                existing_tracks=existing_provider_tracks,
            )

            num_of_added_tracks = len(diff.added)
            num_of_removed_tracks = len(diff.removed)
            num_of_missing_tracks = len(missing_tracks)
            num_of_downloaded_tracks = len(downloaded_tracks)

            if num_of_removed_tracks > 0:
                logger.info(
                    f"Removing {num_of_removed_tracks} outdated songs from "
                    f"{internal_sync.playlist_name} playlist"
                )
                removed_entry_ids = [track.id for track in diff.removed]
                await provider.delete_songs_from_playlist(
                    playlist_id=existing_playlist_id, entry_ids=removed_entry_ids
                )

            if num_of_added_tracks > 0:
                logger.info(
                    f"Adding {num_of_added_tracks} new songs to "
                    f"{internal_sync.playlist_name} playlist"
                )
                added_track_ids = [
                    track.provider_track_id
                    for track in diff.added
                    if track.provider_track_id
                ]
                await provider.add_songs_to_playlist(
                    playlist_id=existing_playlist_id,
                    user_id=provider_user_id,
                    track_ids=added_track_ids,
                )

            spotify_playlist_thumbnail_url = external_playlist.thumbnail_url
            await provider.update_playlist_image(
                playlist_id=existing_playlist_id,
                image_url=spotify_playlist_thumbnail_url
                if spotify_playlist_thumbnail_url.endswith((".png", "jpg", "jpeg"))
                else None,
            )

            finished_at = get_now()
            duration_taken = finished_at.timestamp() - started_at.timestamp()

            discord_webhook_url = get_environment_variable("DISCORD_WEBHOOK_URL")

            if (
                isinstance(discord_webhook_url, str)
                and discord_webhook_url.strip() != ""
            ):
                await send_discord_notification(
                    webhook_url=discord_webhook_url,
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
            removed_track_names = [track.track_name for track in diff.removed]
            missing_track_names = [track.display_name for track in missing_tracks]
            downloaded_track_names = [
                f"{track.artist_name} - {track.album_name}: {track.track_name}"
                for track in downloaded_tracks
            ]

            sync_session.finished_at = finished_at
            sync_session.duration_seconds = int(duration_taken)
            sync_session.status = SyncStatus.completed
            sync_session.tracks = (
                build_sync_session_tracks(
                    sync_session_id=sync_session.id,
                    names=track_names,
                    type=SyncSessionTrackType.total,
                )
                + build_sync_session_tracks(
                    sync_session_id=sync_session.id,
                    names=missing_track_names,
                    type=SyncSessionTrackType.missing,
                )
                + build_sync_session_tracks(
                    sync_session_id=sync_session.id,
                    names=added_track_names,
                    type=SyncSessionTrackType.new,
                )
                + build_sync_session_tracks(
                    sync_session_id=sync_session.id,
                    names=removed_track_names,
                    type=SyncSessionTrackType.outdated,
                )
                + build_sync_session_tracks(
                    sync_session_id=sync_session.id,
                    names=downloaded_track_names,
                    type=SyncSessionTrackType.downloaded,
                )
            )
        except Exception as e:
            if sync_session:
                finished_at = get_now()
                sync_session.status = SyncStatus.failed
                sync_session.finished_at = finished_at
                sync_session.duration_seconds = int(
                    finished_at.timestamp() - started_at.timestamp()
                )
                sync_session.error_message = truncate(text=str(e), max_length=1024)
                sync_session.target_playlist_name = (
                    internal_sync.playlist_name if internal_sync else ""
                )

        finally:
            if sync_session:
                update_sync_session(session=session, sync_session=sync_session)


async def sync_playlist(
    provider: MusicPlaylistProvider, sync_config: Sync
) -> dict[str, str]:
    """Sync a playlist (Spotify/Youtube) to the music provider."""

    with get_isolated_session() as session:
        internal_sync = get_sync_by_id(session=session, sync_id=sync_config.id)

        if not internal_sync:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unable to find sync config: {sync_config.playlist_id}",
            )

        playlist_id = internal_sync.playlist_id
        username = internal_sync.username
        started_at = get_now()

        sync_session = SyncSession(
            provider=internal_sync.provider,
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

        songs: list[ExternalTrack] = []
        external_playlist: ExternalSync | None = None

        match internal_sync.provider:
            case SyncProvider.spotify:
                songs = await asyncio.to_thread(
                    get_spotify_playlist_songs, playlist_id=playlist_id
                )
                external_playlist = await asyncio.to_thread(
                    get_spotify_playlist, playlist_id=playlist_id
                )
            case SyncProvider.youtube:
                songs = await asyncio.to_thread(
                    get_youtube_playlist_songs, playlist_id=playlist_id
                )
                external_playlist = await asyncio.to_thread(
                    get_youtube_playlist, playlist_id=playlist_id
                )

        await sync_playlist_task(
            provider=provider,
            internal_playlist_id=internal_sync.id,
            external_playlist=external_playlist,
            songs=songs,
            sync_session_id=sync_session.id,
        )
        return {"id": str(sync_session.id)}
