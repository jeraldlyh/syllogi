import logging
from typing import Any

import httpx

from lib.env import get_environment_variable
from lib.models.chart import ChartTrendingTrack
from lib.models.metadata import ArtistInfo, ArtistTrack
from lib.providers.metadata.base import MetadataProvider

logger = logging.getLogger(__name__)


class DeezerMetadataProvider(MetadataProvider):
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
        *,
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
        *,
        artist_mbid: str,
        limit: int = 20,
    ) -> list[ArtistTrack]:
        raise NotImplementedError(
            "Deezer does not support fetching recordings by MusicBrainz ID. Use artist_id instead."
        )

    async def get_artist_recording(
        self,
        *,
        artist_name: str,
        track_name: str,
    ) -> ArtistTrack | None:
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

            return ArtistTrack(
                artist_name=artist_name,
                track_name=track.get("title", ""),
                duration_ms=track.get("duration", 0) * 1000,
                disambiguation="",
                album_name=album.get("title", ""),
                genres=[],
                image_url=album.get("cover_big") or album.get("cover_medium"),
            )
        except Exception as e:
            logger.warning(
                f"Failed to fetch Deezer track for '{artist_name} - {track_name}': {e}"
            )
            return None

    async def get_chart_top_tracks(self, limit: int = 50) -> list[ChartTrendingTrack]:
        """Fetch the current top chart tracks from Deezer."""

        try:
            result = await self._http("/chart/0/tracks", params={"limit": limit})

            if not result or not result.get("data"):
                return []

            tracks: list[ChartTrendingTrack] = []

            for track in result.get("data"):
                tracks.append(
                    ChartTrendingTrack(
                        artist_name=track.get("artist", {}).get("name", ""),
                        track_name=track.get("title", ""),
                        album_name=track.get("album", {}).get("title", ""),
                        duration=int(track.get("duration", 0)),
                        listeners=0,
                        playcount=0,
                        musicbrainz_id="",
                        image_url=track.get("album", {}).get("cover_big", ""),
                    )
                )
            return tracks
        except Exception as e:
            logger.error(f"Failed to fetch Deezer chart top tracks: {e}")
            return []
