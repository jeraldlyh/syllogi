import glob
import logging
import os
from pathlib import Path

from lib.common import Track
from lib.youtube import _run_ytdlp

logger = logging.getLogger(__name__)

YOUTUBE_DOWNLOAD_DIR = os.getenv("YOUTUBE_DOWNLOAD_DIR", "/downloads")
DISABLE_MUSIC_VIDEO_DOWNLOADS = (
    os.getenv("DISABLE_MUSIC_VIDEO_DOWNLOADS", "true").lower() == "true"
)


def _get_download_path(artist_name: str, track_name: str, album_name: str = "") -> str:
    """Get the directory path where a song should be downloaded based on artist and album."""

    if album_name:
        return f"{Path(YOUTUBE_DOWNLOAD_DIR)}/{artist_name}/{album_name}/{track_name}"
    return f"{Path(YOUTUBE_DOWNLOAD_DIR)}/{artist_name}/Singles/{track_name}"


def _download_track(
    artist_name: str,
    track_name: str,
    album_name: str = "",
) -> bool:
    """Search YouTube for a song and download it as audio using yt-dlp.

    Returns True if the download succeeded, False otherwise.
    """

    download_path = _get_download_path(artist_name, track_name, album_name)
    existing_paths = glob.glob(f"{glob.escape(download_path)}.*")

    if existing_paths:
        logger.info(
            f"Skipping download for '{artist_name} - {album_name}: {track_name}' as it already exists."
        )
        logger.info(f"Existing file(s) found: {', '.join(existing_paths)}")
        return True

    search_query = f"{artist_name}"
    if album_name:
        search_query += f" {album_name}"
    search_query += f" {track_name}"

    if DISABLE_MUSIC_VIDEO_DOWNLOADS:
        search_query += " lyrics"

    output_template = (
        _get_download_path(artist_name, track_name, album_name) + ".%(ext)s"
    )

    try:
        result = _run_ytdlp(
            url=f"ytsearch:{search_query}",
            opts={
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "opus",
                        "preferredquality": "0",
                    }
                ],
                "outtmpl": output_template,
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
            },
            download=True,
        )

        if (
            len(result["entries"]) > 0
            and len(result["entries"][0]["requested_downloads"]) > 0
            and os.path.exists(
                result["entries"][0]["requested_downloads"][0].get("filepath")
            )
        ):
            title = result.get("title", search_query)
            filepath = result["entries"][0]["requested_downloads"][0].get("filepath")

            logger.info(f"Downloaded: {title} -> {filepath}")
            return True
        logger.warning(f"No results found for: {search_query}")
        return False
    except Exception as e:
        logger.error(f"Failed to download '{search_query}': {e}")
        return False


def _download_missing_tracks(
    missing_tracks: list[Track],
) -> tuple[list[Track], list[Track]]:
    """Download a list of missing songs.

    Returns a tuple containing a list of successfully downloaded songs and a list of still missing track names.
    """

    downloaded_tracks: list[Track] = []
    still_missing_tracks: list[Track] = []

    for song in missing_tracks:
        artist_name = song.artist_name
        track_name = song.track_name
        album_name = song.album_name
        formatted_name = f"{artist_name} - {album_name}: {track_name}"

        success = _download_track(
            artist_name=artist_name,
            track_name=track_name,
            album_name=album_name,
        )

        if success:
            downloaded_tracks.append(song)
            logger.info(f"{formatted_name}: DOWNLOADED")
        else:
            still_missing_tracks.append(song)
            logger.warning(f"{formatted_name}: STILL MISSING")
        break

    return downloaded_tracks, still_missing_tracks
