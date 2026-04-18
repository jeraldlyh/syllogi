import asyncio
import functools
import re
import unicodedata
import string
import glob
import logging
import os
from pathlib import Path

from lib.common import Track
from lib.youtube import _run_ytdlp

logger = logging.getLogger(__name__)

YOUTUBE_DOWNLOAD_DIR = os.getenv("YOUTUBE_DOWNLOAD_DIR", "/downloads")


def _sanitize_filename(name: str) -> str:
    """Sanitize a filename by removing or replacing characters that are not allowed in file names."""

    valid_filename_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned_filename = (
        unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode()
    )
    return "".join(
        char for char in cleaned_filename if char in valid_filename_chars
    ).strip()


def _get_download_path(artist_name: str, track_name: str, album_name: str = "") -> str:
    """Get the directory path where a song should be downloaded based on artist and album."""
    sanitized_artist_name = _sanitize_filename(artist_name)
    sanitized_track_name = _sanitize_filename(track_name)

    if album_name:
        sanitized_album_name = _sanitize_filename(album_name)
        return f"{Path(YOUTUBE_DOWNLOAD_DIR)}/{sanitized_artist_name}/{sanitized_album_name}/{sanitized_track_name}"
    return f"{Path(YOUTUBE_DOWNLOAD_DIR)}/{sanitized_artist_name}/Singles/{sanitized_track_name}"


def _score_video(entry):
    """Score a YouTube video entry based on heuristics to determine its suitability as a download candidate."""

    score = 0.0
    title = (entry.get("title") or "").lower()
    uploader = (entry.get("uploader") or "").lower()

    if "official audio" in title:
        score += 0.5
    if "audio" in title:
        score += 0.3
    if any(term in uploader for term in ["official", "music video"]):
        score += 0.2

    score += min(entry.get("view_count") or 0, 1_000_000) // 1_000_000
    return score


def _is_lyrics_video(entry: dict) -> bool:
    """Determine if a video is a lyric video based on its title."""

    title = (entry.get("title") or "").lower()
    return bool(re.search(r"\blyrics?\b|\blyric video\b", title))


def _is_bad_fallback(entry) -> bool:
    """Determine if a video is a bad fallback option based on its title."""

    title = (entry.get("title") or "").lower()
    bad_patterns = [
        r"\blive\b",
    ]
    return any(re.search(pattern, title) for pattern in bad_patterns)


def _get_best_entry(entries: list[dict]) -> dict | None:
    """Get the best entry from a list of yt-dlp search results based on heuristics."""

    lyrics_candidates = []
    fallback_candidates = []

    for entry in entries:
        if not entry:
            continue

        if entry.get("is_live"):
            continue

        if _is_lyrics_video(entry):
            lyrics_candidates.append(entry)
            continue

        if not _is_bad_fallback(entry):
            fallback_candidates.append(entry)

    if lyrics_candidates:
        return max(lyrics_candidates, key=lambda e: e.get("view_count") or 0)

    if fallback_candidates:
        return max(fallback_candidates, key=_score_video)
    return None


async def download_track(
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

    output_path = _get_download_path(artist_name, track_name, album_name)
    output_template = output_path + ".%(ext)s"

    try:
        search_results = _run_ytdlp(
            url=f"ytsearch5:{search_query}",
            opts={
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "skip_download": "",
            },
        )
        best_entry = _get_best_entry(search_results.get("entries", []))
        best_entry_url = best_entry.get("webpage_url") if best_entry else None

        if not best_entry or not best_entry_url:
            logger.warning(f"No suitable YouTube entry found for: {search_query}")
            return False

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            functools.partial(
                _run_ytdlp,
                url=best_entry_url,
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
                    "sleep_interval": 10,
                    "max_sleep_interval": 30,
                    "sleep_interval_requests": 10,
                },
                download=True,
            ),
        )
        # _run_ytdlp(
        #     url=f"ytsearch:{best_entry_url}",
        #     opts={
        #         "format": "bestaudio/best",
        #         "postprocessors": [
        #             {
        #                 "key": "FFmpegExtractAudio",
        #                 "preferredcodec": "opus",
        #                 "preferredquality": "0",
        #             }
        #         ],
        #         "outtmpl": output_template,
        #         "quiet": True,
        #         "no_warnings": True,
        #         "noplaylist": True,
        #         "sleep_interval": 10,
        #         "max_sleep_interval": 30,
        #         "sleep_interval_requests": 10,
        #     },
        #     download=True,
        # )

        downloaded_file_path = glob.glob(f"{glob.escape(output_path)}.*")

        if downloaded_file_path:
            title = best_entry.get("title", search_query)

            logger.info(f"Downloaded: {title} -> {downloaded_file_path}")
            return True
        logger.warning(f"No results found for: {search_query}")
        return False
    except Exception as e:
        logger.error(f"Failed to download '{search_query}': {e}")
        return False


async def download_missing_tracks(
    missing_tracks: list[Track],
) -> tuple[list[Track], list[Track]]:
    """Download a list of missing songs.

    Returns a tuple containing a list of successfully downloaded songs and a list of still missing track names.
    """

    logger.info(f"Attempting to download {len(missing_tracks)} missing tracks...")

    downloaded_tracks: list[Track] = []
    still_missing_tracks: list[Track] = []

    for song in missing_tracks:
        artist_name = song.artist_name
        track_name = song.track_name
        album_name = song.album_name
        formatted_name = f"{artist_name} - {album_name}: {track_name}"

        success = await download_track(
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
