import logging
from typing import Any

import httpx

from lib.env import get_environment_variable
from lib.models.chart import ChartTrendingTrack
from lib.models.metadata import ArtistInfo, ArtistTrack
from lib.providers.metadata.base import MetadataProvider

logger = logging.getLogger(__name__)


class LastFMMetadataProvider(MetadataProvider):
    """Metadata provider backed by the Last.fm API."""

    async def _http(
        self,
        path: str = "",
        method: str = "GET",
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> Any:
        """HTTP helper for the Last.fm API."""

        base_headers = {
            "Content-Type": "application/json",
        }
        api_key = get_environment_variable("LASTFM_API_KEY", ignore_error=False)
        api_url = get_environment_variable("LASTFM_URL", ignore_error=False)

        default_params = {
            "api_key": api_key,
            "format": "json",
        }
        default_params.update(params or {})

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method.upper(),
                url=f"{api_url}{path}",
                headers={**base_headers, **(headers or {})},
                params={**default_params},
                timeout=timeout,
            )
        response.raise_for_status()

        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def _get_nested_value(self, data: Any, path: str) -> Any:
        value: Any = data

        for key in path.split("."):
            if not isinstance(value, dict):
                return None
            value = value.get(key)
        return value

    async def get_artist_info(
        self,
        *,
        artist_name: str,
        locale: str | None = None,
    ) -> ArtistInfo | None:
        data = await self._http(
            params={
                "method": "artist.getInfo",
                "artist": artist_name,
            },
        )
        if not data:
            return None

        artist = data.get("artist")

        if not artist:
            return None

        mbid = artist.get("mbid", "")
        name = artist.get("name", "")

        raw_tags = self._get_nested_value(artist, "tags.tag") or []
        tags = [tag.get("name", "") for tag in raw_tags]

        return ArtistInfo(
            id=mbid,
            name=name,
            type="",
            country="",
            gender="",
            life_span={},
            area=None,
            begin_area=None,
            tags=tags,
            aliases=[],
        )

    async def get_artist_recordings(
        self,
        *,
        artist_mbid: str,
        limit: int = 20,
    ) -> list[ArtistTrack]:
        info = await self._http(
            params={
                "method": "artist.getInfo",
                "mbid": artist_mbid,
            },
        )
        if not info:
            return []

        artist = info.get("artist")

        if not artist:
            return []

        artist_name = artist.get("name", "")

        if not artist_name:
            return []

        data = await self._http(
            params={
                "method": "artist.getTopTracks",
                "artist": artist_name,
                "limit": limit,
            },
        )
        raw_tracks = self._get_nested_value(data, "toptracks.track") or []
        tracks: list[ArtistTrack] = []
        for raw_track in raw_tracks:
            duration = int(raw_track.get("duration", 0) or 0)

            if not duration:
                continue

            tracks.append(
                ArtistTrack(
                    track_name=raw_track.get("name", ""),
                    duration_ms=duration * 1000,
                    disambiguation="",
                    album_name="",
                    genres=[],
                    image_url="",
                )
            )
        return tracks

    async def get_artist_recording(
        self,
        *,
        artist_name: str,
        track_name: str,
    ) -> ArtistTrack | None:
        data = await self._http(
            params={
                "method": "artist.search",
                "track": track_name,
                "artist": artist_name,
                "limit": 5,
            },
        )
        if not data:
            return None

        tracks = self._get_nested_value(data, "results.trackmatches.track") or []

        for track in tracks:
            lower_artist_name = track.get("artist", "").casefold()
            lower_track_title = track.get("name", "").casefold()

            if (
                lower_artist_name == artist_name.casefold()
                and track_name.casefold() in lower_track_title
            ):
                duration = int(track.get("duration", 0) or 0)

                return ArtistTrack(
                    track_name=track.get("name", ""),
                    duration_ms=duration * 1000 if duration else None,
                    disambiguation="",
                    album_name="",
                    genres=[],
                    image_url="",
                )
        return None

    async def get_chart_top_tracks(self, limit: int = 50) -> list[ChartTrendingTrack]:
        data = await self._http(
            params={
                "method": "chart.getTopTracks",
                "limit": limit,
            },
        )
        raw_tracks = self._get_nested_value(data, "tracks.track") or []
        tracks: list[ChartTrendingTrack] = []

        for raw_track in raw_tracks:
            tracks.append(
                ChartTrendingTrack(
                    artist_name=raw_track.get("artist", {}).get("name", ""),
                    track_name=raw_track.get("name", ""),
                    album_name="",
                    duration=int(raw_track.get("duration", 0) or 0),
                    listeners=int(raw_track.get("listeners", 0) or 0),
                    playcount=int(raw_track.get("playcount", 0) or 0),
                    musicbrainz_id=raw_track.get("mbid", ""),
                    image_url="",
                )
            )
        return tracks
