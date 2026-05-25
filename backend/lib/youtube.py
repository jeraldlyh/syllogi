from __future__ import annotations

import asyncio
import functools
import glob
import logging
import re
from typing import TYPE_CHECKING, Any

import yt_dlp

from lib.models.common import ExternalPlaylist, ExternalTrack
from lib.env import get_environment_variable
from lib.utils import dump_results, get_download_path, normalize

if TYPE_CHECKING:
    from yt_dlp import _Params

logger = logging.getLogger(__name__)

IS_DEVELOPMENT = get_environment_variable("IS_DEVELOPMENT")


def _ytdlp(url: str, opts: _Params | None = None, *, download: bool = False) -> Any:
    """Run yt-dlp with the given URL and options."""

    default_opts: _Params = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
    }
    if opts:
        default_opts.update(opts)

    with yt_dlp.YoutubeDL(params=default_opts) as ydl:
        logger.debug(f"Running yt-dlp for URL: {url} with options: {default_opts}")
        if download:
            logger.info(f"Downloading content from URL: {url}")
            ydl.download([url])
            return None

        logger.info(f"Extracting information from URL: {url}")
        result = ydl.extract_info(url, download=download)

        if IS_DEVELOPMENT:
            dump_results(f"yt-dlp-{url}", dict(result))
        return result


def get_youtube_playlist(playlist_id: str) -> ExternalPlaylist:
    """Fetch YouTube playlist metadata."""

    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    playlist = _ytdlp(
        url,
        {
            "extract_flat": True,
            "skip_download": "",
            "ignoreerrors": True,
        },
    )

    if IS_DEVELOPMENT:
        dump_results(f"youtube-{playlist_id}", playlist)

    return ExternalPlaylist(
        id=playlist.get("id", ""),
        name=playlist.get("title", ""),
        thumbnail_url=playlist.get("thumbnails", [{}])[-1].get("url", ""),
        total=len(playlist.get("entries", [])),
    )


def get_youtube_playlist_songs(playlist_id: str) -> list[ExternalTrack]:
    """Fetch full metadata for every track in a YouTube playlist."""
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    playlist = _ytdlp(
        url,
        {
            "extract_flat": True,
            "skip_download": "",
            "ignoreerrors": True,
        },
    )

    songs: list[ExternalTrack] = []
    for entry in playlist.get("entries", []):
        # NOTE: Ignore private or deleted videos that don't have metadata
        if entry.get("channel") is None or entry.get("title") is None:
            continue

        artist_name = entry.get("channel", "")
        track_name = (
            entry.get("title", "")
            if artist_name not in entry.get("title", "")
            # NOTE: Some songs contain either dash or en dash
            else re.sub(
                f"^{re.escape(artist_name)}\\s*[-–]\\s*", "", entry.get("title", "")
            )
        )
        duration = entry.get("duration") or 0

        song = ExternalTrack(
            track_name=track_name,
            artist_name=artist_name,
            album_name="",
            year="",
            duration=int(duration),
        )
        songs.append(song)
    logger.info(f"Total songs fetched from YouTube playlist: {len(songs)}")
    return songs


def _score_entry(entry: dict) -> float:
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
        return max(fallback_candidates, key=_score_entry)
    return None


async def download_track_youtube(
    artist_name: str,
    track_name: str,
    album_name: str = "",
) -> bool:
    """Search YouTube for a song and download it as audio using yt-dlp.

    Returns True if the download succeeded, False otherwise.
    """

    search_query = f"{artist_name}"
    if album_name and normalize(text=album_name) != normalize(text=track_name):
        search_query += f" {album_name}"
    search_query += f" {track_name}"

    output_path = get_download_path(artist_name, track_name, album_name)
    logger.info(f"output_path: {output_path}")
    output_template = output_path + ".%(ext)s"

    try:
        search_results = _ytdlp(
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
                _ytdlp,
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
