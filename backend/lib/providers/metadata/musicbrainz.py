import asyncio
import logging
from typing import Any

import httpx

from lib.env import get_environment_variable
from lib.models.musicbrainz import (
    MusicbrainzArtist,
    MusicbrainzArtistAlias,
    MusicbrainzArtistArea,
    MusicbrainzArtistTag,
)
from lib.models.metadata import ArtistTrack
from lib.providers.metadata.base import (
    ArtistInfo,
    MetadataProvider,
)

logger = logging.getLogger(__name__)


class MusicBrainzMetadataProvider(MetadataProvider):
    """Metadata provider backed by the MusicBrainz API."""

    SEARCH_MAX_RETRIES = 3
    SEARCH_POLL_INTERVAL = 10

    async def _http(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """HTTP helper for MusicBrainz API."""

        url = str(get_environment_variable("MUSICBRAINZ_URL")) + path
        headers = {
            "User-Agent": str(get_environment_variable("MUSICBRAINZ_USER_AGENT")),
        }

        query_params = {"fmt": "json", **(params or {})}

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=query_params, headers=headers)
            response.raise_for_status()

            if response.content:
                return response.json()
            return None

    async def _get_artists(
        self,
        *,
        artist_name: str,
        limit: int = 10,
    ) -> list[MusicbrainzArtist]:
        """Search MusicBrainz for artists by name. Returns a list of artist matches."""

        result = await self._http(
            "/artist", params={"query": artist_name, "limit": limit, "inc": "aliases"}
        )

        return [
            MusicbrainzArtist(
                id=artist.get("id"),
                type=artist.get("type"),
                type_id=artist.get("type-id"),
                score=artist.get("score"),
                gender_id=artist.get("gender-id"),
                name=artist.get("name"),
                sort_name=artist.get("sort-name"),
                gender=artist.get("gender"),
                country=artist.get("country"),
                area=MusicbrainzArtistArea(
                    id=artist.get("area", {}).get("id"),
                    type=artist.get("area", {}).get("type"),
                    type_id=artist.get("area", {}).get("type-id"),
                    name=artist.get("area", {}).get("name"),
                    sort_name=artist.get("area", {}).get("sort-name"),
                    life_span=artist.get("area", {}).get("life-span"),
                ),
                begin_area=MusicbrainzArtistArea(
                    id=artist.get("begin-area", {}).get("id"),
                    type=artist.get("begin-area", {}).get("type"),
                    type_id=artist.get("begin-area", {}).get("type-id"),
                    name=artist.get("begin-area", {}).get("name"),
                    sort_name=artist.get("begin-area", {}).get("sort-name"),
                    life_span=artist.get("begin-area", {}).get("life-span"),
                ),
                ipis=artist.get("ipis"),
                isnis=artist.get("isnis"),
                life_span=artist.get("life-span"),
                aliases=[
                    MusicbrainzArtistAlias(
                        sort_name=alias.get("sort-name"),
                        name=alias.get("name"),
                        locale=alias.get("locale"),
                        type=alias.get("type"),
                        primary=alias.get("primary"),
                        begin_date=alias.get("begin-date"),
                        end_date=alias.get("end-date"),
                    )
                    for alias in artist.get("aliases", [])
                ],
                tags=[
                    MusicbrainzArtistTag(
                        count=tag.get("count"),
                        name=tag.get("name"),
                    )
                    for tag in artist.get("tags", [])
                ],
            )
            for artist in result.get("artists", [])
        ]

    async def get_artist_recordings(
        self,
        *,
        artist_mbid: str,
    ) -> list[ArtistTrack]:
        """Fetch recordings by artist MusicBrainz ID."""

        result = await self._http(
            f"/artist/{artist_mbid}",
            params={
                "inc": "recordings",
            },
        )

        if not result:
            return []

        unique = set()
        for recording in result.get("recordings", []):
            if not recording.get("length"):
                continue
            unique.add(
                ArtistTrack(
                    title=recording.get("title", ""),
                    duration_ms=recording.get("length"),
                    disambiguation=recording.get("disambiguation", ""),
                    album_name="",
                )
            )
        return list(unique)

    async def get_artist_info(
        self,
        *,
        artist_name: str,
        locale: str | None = None,
    ) -> ArtistInfo | None:
        """Search MusicBrainz for artist by name."""

        results = await self._get_artists(artist_name=artist_name, limit=1)

        if not results:
            return None
        return results[0].to_artist_info(locale=locale)

    async def get_artist_alias(self, *, artist_name: str) -> str | None:
        """Get artist actual name using MusicBrainz.

        This is useful for artists with non-Latin names, but has an English name as an alias.

        For example, Spotify returns "Joker Xue" as an alias for "薛之谦".
        """

        for attempt in range(1, self.SEARCH_MAX_RETRIES + 1):
            try:
                artists = await self._get_artists(artist_name=artist_name)

                if artists:
                    return artists[0].name

                logger.warning(
                    f"[{attempt}/{self.SEARCH_MAX_RETRIES}] Retry search for artist '{artist_name}' but got no results."
                )
            except Exception as e:
                logger.error(
                    f"[{attempt}/{self.SEARCH_MAX_RETRIES}] Failed to search for artist '{artist_name}': {e}"
                )

            if attempt < self.SEARCH_MAX_RETRIES:
                await asyncio.sleep(self.SEARCH_POLL_INTERVAL)
        return None
