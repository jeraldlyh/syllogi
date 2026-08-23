import logging
from typing import Any

import httpx

from lib.env import get_environment_variable
from lib.models.library import LyricsCandidate
from lib.providers.lyrics.base import MAX_SEARCH_RESULTS, LyricsProvider

logger = logging.getLogger(__name__)


class LRCLIBLyricsProvider(LyricsProvider):
    """Fetches lyrics from the LRCLIB API."""

    DURATION_TOLERANCE_SECONDS = 2

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

    async def search_lyrics(
        self,
        *,
        query: str = "",
        artist_name: str = "",
        track_name: str = "",
        album_name: str = "",
        limit: int = MAX_SEARCH_RESULTS,
    ) -> list[LyricsCandidate]:
        """Search LRCLIB for lyrics matching a track, returning every candidate.

        Pass either a free-text query, or a track name with an optional artist
        and album to narrow the search.
        """

        params: dict[str, Any] = {}

        if query:
            params["q"] = query
        else:
            if not track_name:
                return []

            params["track_name"] = track_name

            if artist_name:
                params["artist_name"] = artist_name
            if album_name:
                params["album_name"] = album_name

        try:
            results = await self._http("/search", params=params)
        except httpx.HTTPError as e:
            logger.warning(f"Failed to search LRCLIB for '{track_name}': {e}")
            return []

        if not results:
            return []

        return [
            LyricsCandidate(
                id=result.get("id", 0),
                track_name=result.get("trackName") or "",
                artist_name=result.get("artistName") or "",
                album_name=result.get("albumName") or "",
                duration=int(result.get("duration") or 0),
                instrumental=bool(result.get("instrumental")),
                plain_lyrics=(result.get("plainLyrics") or "").strip(),
                synced_lyrics=(result.get("syncedLyrics") or "").strip(),
            )
            for result in results[:limit]
        ]

    def select_lyrics(
        self, *, candidates: list[LyricsCandidate], duration: int = 0
    ) -> str:
        """Pick the lyrics to write to a file from a set of LRCLIB candidates.

        Instrumental and empty candidates are skipped. When the track's duration is
        known, only candidates recorded at the same length are considered, which is
        the tolerance LRCLIB itself applies when matching a track. Synced lyrics
        win over plain ones.

        Returns the chosen lyrics, or an empty string when nothing matches.
        """

        usable = [
            candidate
            for candidate in candidates
            if not candidate.instrumental
            and (candidate.synced_lyrics or candidate.plain_lyrics)
        ]

        if duration:
            usable = [
                candidate
                for candidate in usable
                if abs(candidate.duration - duration) <= self.DURATION_TOLERANCE_SECONDS
            ]

        if not usable:
            return ""

        result = next(
            (candidate for candidate in usable if candidate.synced_lyrics), None
        )

        if result:
            return result.synced_lyrics
        return usable[0].plain_lyrics
