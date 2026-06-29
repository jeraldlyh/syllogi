import logging
from typing import Any

import httpx

from lib.env import get_environment_variable
from lib.models.deezer import DeezerTrack
from lib.models.metadata import ArtistInfo, ArtistRecording
from lib.providers.metadata.base import MetadataSourceProvider

logger = logging.getLogger(__name__)


class DeezerMetadataProvider(MetadataSourceProvider):
    """Metadata provider backed by the Deezer API."""

    async def _http(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """HTTP helper for Deezer API."""

        url = f"{get_environment_variable('DEEZER_URL')}{path}"

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            if response.content:
                return response.json()
            return None

    async def get_artist_info(
        self,
        artist_name: str,
    ) -> ArtistInfo | None:
        """Search Deezer for artist by name."""

        try:
            result = await self._http(
                "/search/artist", params={"q": artist_name, "limit": 1}
            )

            if not result or not result.get("data"):
                return None

            artist = result["data"][0]

            return ArtistInfo(
                id=str(artist.get("id", "")),
                name=artist.get("name", ""),
                type="",
                country="",
                gender="",
                life_span={},
                area=None,
                begin_area=None,
                tags=[],
                aliases=[],
                image_url=artist.get("picture_big") or artist.get("picture_medium"),
                num_of_fans=artist.get("nb_fan"),
            )
        except Exception as e:
            logger.error(f"Failed to fetch Deezer artist info for '{artist_name}': {e}")
            return None

    async def get_artist_recordings(
        self,
        artist_id: str,
        limit: int = 20,
    ) -> list[ArtistRecording]:
        """Get top tracks for an artist from Deezer."""

        try:
            result = await self._http(
                f"/artist/{artist_id}/top", params={"limit": limit}
            )

            if not result or not result.get("data"):
                return []

            return [
                ArtistRecording(
                    title=track.get("title", ""),
                    duration_ms=track.get("duration", 0) * 1000,
                    disambiguation="",
                    album_name=track.get("album", {}).get("title", ""),
                )
                for track in result["data"]
            ]
        except Exception as e:
            logger.error(
                f"Failed to fetch Deezer recordings for artist '{artist_id}': {e}"
            )
            return []

    async def get_track(
        self,
        artist_name: str,
        track_name: str,
    ) -> DeezerTrack | None:
        """Search Deezer for a track and return its metadata."""

        try:
            result = await self._http(
                "/search/track",
                params={"q": f"{artist_name} {track_name}", "limit": 1},
            )

            if not result or not result.get("data"):
                return None

            track = result["data"][0]
            album = track.get("album", {})

            return DeezerTrack(
                title=track.get("title", ""),
                album_name=album.get("title", ""),
                image_url=album.get("cover_big") or album.get("cover_medium"),
                duration=track.get("duration", 0),
            )
        except Exception as e:
            logger.warning(
                f"Failed to fetch Deezer track for '{artist_name} - {track_name}': {e}"
            )
            return None
