import logging

from lib.models.common import ExternalTrack
from lib.env import get_environment_variable
from lib.slskd import download_track_slskd
from lib.utils import is_track_exists
from lib.youtube import download_track_youtube

logger = logging.getLogger(__name__)


async def download_missing_tracks(
    missing_tracks: list[ExternalTrack],
) -> tuple[list[ExternalTrack], list[ExternalTrack]]:
    """Download a list of missing songs.

    Attempts to download each track in the following order:
    1. slskd (if SLSKD_URL is configured)
    2. yt-dlp (fallback)

    Returns a tuple of (successfully downloaded, still missing).
    """
    slskd_url = get_environment_variable("SLSKD_URL")
    use_slskd = bool(slskd_url)

    logger.info(f"Attempting to download {len(missing_tracks)} missing tracks...")

    downloaded_tracks: list[ExternalTrack] = []
    still_missing_tracks: list[ExternalTrack] = []

    for song in missing_tracks:
        artist_name = song.artist_name
        track_name = song.track_name
        album_name = song.album_name
        duration = song.duration
        formatted_name = f"{artist_name} - {album_name}: {track_name}"

        if is_track_exists(
            artist_name=artist_name, track_name=track_name, album_name=album_name
        ):
            logger.info(f"{formatted_name}: ALREADY EXISTS")
            continue

        is_download_success = False

        if use_slskd:
            logger.info(f"Downloading with slskd: {formatted_name}")
            is_download_success = await download_track_slskd(
                artist_name=artist_name,
                track_name=track_name,
                album_name=album_name,
                duration=duration,
            )

        if not is_download_success:
            if use_slskd:
                logger.info(
                    f"slskd failed, falling back to yt-dlp for: {formatted_name}"
                )
            is_download_success = await download_track_youtube(
                artist_name=artist_name,
                track_name=track_name,
                album_name=album_name,
            )

        if is_download_success:
            downloaded_tracks.append(song)
            logger.info(f"{formatted_name}: DOWNLOADED")
        else:
            still_missing_tracks.append(song)
            logger.warning(f"{formatted_name}: STILL MISSING")

    return downloaded_tracks, still_missing_tracks
