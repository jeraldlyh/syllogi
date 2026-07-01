import logging
import os
import uuid

from fastapi import HTTPException, status

from db.download_session import get_download_session_by_id, update_download_session
from db.models.download_session import DownloadSession, DownloadSessionStatus
from db.session import get_isolated_session
from lib.env import is_slskd_configured
from lib.models.common import ExternalTrack
from lib.models.provider import ProviderTrack
from lib.providers.metadata.musicbrainz import MusicBrainzMetadataProvider
from lib.providers.playlist.base import MusicPlaylistProvider
from lib.slskd import download_track_slskd
from lib.tagger import tag_audio_file
from lib.utils import (
    get_existing_track_path,
    get_now,
    is_track_exists_in_path,
    is_track_lossless,
    truncate,
)
from lib.track import find_track
from lib.youtube import download_track_youtube

logger = logging.getLogger(__name__)


async def download_missing_tracks(
    *,
    missing_tracks: list[ExternalTrack],
) -> tuple[list[ExternalTrack], list[ExternalTrack]]:
    """Download a list of missing songs.

    Attempts to download each track in the following order:
    1. slskd
    2. yt-dlp (fallback)

    Returns a tuple of (successfully downloaded, still missing).
    """
    logger.info(f"Attempting to download {len(missing_tracks)} missing tracks...")

    is_slskd_enabled = is_slskd_configured()
    found_tracks_after_download: list[ExternalTrack] = []
    missing_tracks_after_download: list[ExternalTrack] = []

    for song in missing_tracks:
        artist_name = song.artist_name
        track_name = song.track_name
        album_name = song.album_name
        duration = song.duration

        if album_name is None:
            formatted_name = f"{artist_name} {track_name}"
        else:
            formatted_name = f"{artist_name} {album_name}: {track_name}"

        if is_track_exists_in_path(
            artist_name=artist_name, track_name=track_name, album_name=album_name
        ):
            logger.info(f"{formatted_name}: ALREADY EXISTS")
            found_tracks_after_download.append(song)
            continue

        is_download_success = False

        if is_slskd_enabled:
            logger.info(f"Downloading with slskd: {formatted_name}")
            is_download_success = await download_track_slskd(
                artist_name=artist_name,
                track_name=track_name,
                album_name=album_name,
                duration=duration,
            )

        if not is_download_success:
            if is_slskd_enabled:
                logger.info(
                    f"slskd failed, falling back to yt-dlp for: {formatted_name}"
                )
            is_download_success = await download_track_youtube(
                artist_name=artist_name,
                track_name=track_name,
                album_name=album_name,
            )

        if is_download_success:
            found_tracks_after_download.append(song)
            existing_path = get_existing_track_path(
                artist_name=artist_name, track_name=track_name, album_name=album_name
            )

            if existing_path:
                provider = MusicBrainzMetadataProvider()
                mb_track = await provider.get_artist_recording(
                    artist_name=artist_name, track_name=track_name
                )
                tag_audio_file(
                    file_path=existing_path,
                    artist_name=artist_name,
                    track_name=mb_track.title if mb_track else track_name,
                    album_name=mb_track.album_name if mb_track else album_name,
                    year=song.year,
                    genres=mb_track.genres if mb_track else [],
                )
            logger.info(f"{formatted_name}: DOWNLOADED")
        else:
            missing_tracks_after_download.append(song)
            logger.warning(f"{formatted_name}: STILL MISSING")

    return found_tracks_after_download, missing_tracks_after_download


async def upgrade_non_lossless_tracks(
    *,
    tracks: list[ProviderTrack],
) -> list[ProviderTrack]:
    """Attempt to upgrade non-lossless tracks to FLAC via slskd.

    For each track that exists on disk in a non-lossless format, the old file is
    deleted before attempting the FLAC download. If the download fails, the track
    will be re-downloaded from scratch on the next sync.

    Returns a list of tracks that were successfully upgraded.
    """
    if not is_slskd_configured():
        return []

    upgraded: list[ProviderTrack] = []

    for track in tracks:
        artist_name = track.artists[0] if track.artists else ""
        track_name = track.track_name
        album_name = track.album_name
        duration = int(track.duration_ticks / 10_000_000) if track.duration_ticks else 0
        formatted_name = f"{artist_name} - {album_name}: {track_name}"

        if not is_track_exists_in_path(
            artist_name=artist_name, track_name=track_name, album_name=album_name
        ):
            continue

        if is_track_lossless(
            artist_name=artist_name, track_name=track_name, album_name=album_name
        ):
            continue

        existing_path = get_existing_track_path(
            artist_name=artist_name, track_name=track_name, album_name=album_name
        )

        if not existing_path:
            continue

        try:
            os.remove(existing_path)
            logger.info(f"{formatted_name}: Removed non-lossless file for upgrade")
        except OSError as e:
            logger.warning(
                f"{formatted_name}: Failed to remove non-lossless file, skipping upgrade: {e}"
            )
            continue

        logger.info(f"{formatted_name}: Attempting lossless upgrade via slskd")

        is_success = await download_track_slskd(
            artist_name=artist_name,
            track_name=track_name,
            album_name=album_name,
            duration=duration,
            lossless_only=True,
        )

        if is_success:
            upgraded.append(track)
            logger.info(f"{formatted_name}: UPGRADED TO LOSSLESS")
        else:
            logger.info(f"{formatted_name}: LOSSLESS UPGRADE FAILED")

    return upgraded


async def download_single_track(
    *,
    provider: MusicPlaylistProvider,
    download_session_id: uuid.UUID,
    track: ExternalTrack,
) -> None:
    """Download a single chart track."""

    download_session: DownloadSession | None = None

    with get_isolated_session() as session:
        try:
            download_session = get_download_session_by_id(session, download_session_id)
            if not download_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Unable to find download session with ID: {download_session_id}",
                )

            download_session.status = DownloadSessionStatus.downloading
            update_download_session(session, download_session)

            is_exist_locally = is_track_exists_in_path(
                artist_name=track.artist_name,
                track_name=track.track_name,
                album_name=track.album_name,
            )

            if is_exist_locally:
                provider_track = await find_track(
                    provider=provider,
                    artist_name=track.artist_name,
                    track_name=track.track_name,
                    album_name=track.album_name,
                    year=track.year,
                    duration=track.duration,
                )
                if provider_track.is_not_found():
                    await provider.rescan_library()
                download_session.status = DownloadSessionStatus.existed
            else:
                found, _ = await download_missing_tracks(missing_tracks=[track])

                if found:
                    await provider.rescan_library()

                download_session.status = (
                    DownloadSessionStatus.completed
                    if found
                    else DownloadSessionStatus.failed
                )

            download_session.finished_at = get_now()

        except Exception as e:
            if download_session:
                download_session.status = DownloadSessionStatus.failed
                download_session.finished_at = get_now()
                download_session.error_message = truncate(text=str(e), max_length=1024)
        finally:
            if download_session:
                update_download_session(session, download_session)
