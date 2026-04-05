from __future__ import annotations

import logging
import os
import re
from typing import TYPE_CHECKING, Any

import yt_dlp

from lib.common import ExternalPlaylist, Track
from lib.utils import _dump_results

if TYPE_CHECKING:
    from yt_dlp import _Params

logger = logging.getLogger(__name__)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
IS_DEVELOPMENT = os.getenv("ENVIRONMENT", "production") == "development"


def _run_ytdlp(url: str, opts: _Params | None = None, *, download: bool = False) -> Any:
    """Run yt-dlp with the given URL and options."""

    default_opts: _Params = {
        "quiet": True,
        "no_warnings": True,
        "sleep_interval": 1,
    }
    if opts:
        default_opts.update(opts)

    with yt_dlp.YoutubeDL(params=default_opts) as ydl:
        logger.debug(f"Running yt-dlp for URL: {url} with options: {default_opts}")
        result = ydl.extract_info(url, download=download)

        if IS_DEVELOPMENT:
            _dump_results("yt-dlp", dict(result))
        return result


def _get_youtube_playlist(playlist_id: str) -> ExternalPlaylist:
    """Fetch YouTube playlist metadata."""

    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    playlist = _run_ytdlp(
        url,
        {
            "extract_flat": True,
            "skip_download": "",
            "ignoreerrors": True,
        },
    )

    if IS_DEVELOPMENT:
        _dump_results("youtube", playlist)

    return ExternalPlaylist(
        id=playlist.get("id", ""),
        name=playlist.get("title", ""),
        thumbnail_url=playlist.get("thumbnails", [{}])[-1].get("url", ""),
        total=len(playlist.get("entries", [])),
    )


def _get_youtube_playlist_songs(playlist_id: str) -> list[Track]:
    """Fetch full metadata for every track in a YouTube playlist."""
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    playlist = _run_ytdlp(
        url,
        {
            "extract_flat": True,
            "skip_download": "",
            "ignoreerrors": True,
        },
    )

    songs: list[Track] = []
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

        song = Track(
            track_name=track_name,
            artist_name=artist_name,
            album_name="",
            year="",
            duration=int(duration),
        )
        songs.append(song)
    logger.info(f"Total songs fetched from YouTube playlist: {len(songs)}")
    return songs
