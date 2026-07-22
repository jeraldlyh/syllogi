import logging
from typing import Any

import httpx

from lib.env import get_environment_variable
from lib.providers.lyrics.base import LyricsProvider

logger = logging.getLogger(__name__)


class LRCLIBLyricsProvider(LyricsProvider):
    """Fetches lyrics from the LRCLIB API."""

    async def _http(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """HTTP helper for the LRCLIB API."""

        url = f"{get_environment_variable('LRCLIB_URL')}{path}"

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            if response.content:
                return response.json()
            return None

    async def get_lyrics(
        self,
        *,
        artist_name: str,
        track_name: str,
        album_name: str,
        duration: int,
    ) -> str | None:
        """Fetch lyrics for a track."""

        params: dict[str, Any] = {
            "artist_name": artist_name,
            "track_name": track_name,
            "album_name": album_name,
            "duration": duration,
        }

        try:
            data = await self._http("/get", params=params)
            if not data:
                return None

            plain_lyrics = data.get("syncedLyrics")

            if plain_lyrics:
                return plain_lyrics.strip()
            return None
        except Exception as e:
            logger.warning(
                f"Failed to fetch lyrics from LRCLIB for '{artist_name} - {track_name}': {e}"
            )
            return None
