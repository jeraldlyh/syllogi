import logging
import os
from pathlib import Path

from lib.common import Song
from lib.youtube import _run_ytdlp

logger = logging.getLogger(__name__)

YOUTUBE_DOWNLOAD_DIR = os.getenv("YOUTUBE_DOWNLOAD_DIR", "/downloads")


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

    search_query = f"{artist_name} - {track_name}"
    if album_name:
        search_query += f" {album_name}"

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

        if result:
            title = result.get("title", search_query)
            logger.info(f"Downloaded: {title} -> {output_template}")
            return True
        logger.warning(f"No results found for: {search_query}")
        return False
    except Exception as e:
        logger.error(f"Failed to download '{search_query}': {e}")
        return False


def _download_missing_tracks(
    missing_tracks: list[Song],
) -> tuple[list[Song], list[Song]]:
    """Download a list of missing songs.

    Returns a tuple containing a list of successfully downloaded songs and a list of still missing track names.
    """

    downloaded_tracks: list[Song] = []
    still_missing_tracks: list[Song] = []

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

    return downloaded_tracks, still_missing_tracks
