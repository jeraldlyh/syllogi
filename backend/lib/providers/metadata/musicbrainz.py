from __future__ import annotations

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
    MusicbrainzRecording,
)
from lib.providers.metadata.base import (
    ArtistInfo,
    MetadataSourceProvider,
)

logger = logging.getLogger(__name__)


class MusicBrainzMetadataProvider(MetadataSourceProvider):
    """Metadata provider backed by the MusicBrainz API."""

    SEARCH_MAX_RETRIES = 3
    SEARCH_POLL_INTERVAL = 10

    SUB_QUERIES: dict[str, str] = {
        "enableRecordings": "recordings",
        "enableAliases": "aliases",
    }

    async def _http(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Make a request to the MusicBrainz API."""

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
        artist_name: str,
        limit: int = 10,
        options: dict[str, bool] | None = None,
    ) -> list[MusicbrainzArtist]:
        """Search MusicBrainz for artists by name. Returns a list of artist matches."""

        params = {"query": artist_name, "limit": limit}
        result = await self._http("/artist", params=params)

        paths: list[str] = []
        if options:
            for key, enabled in options.items():
                if enabled and key in self.SUB_QUERIES:
                    paths.append(self.SUB_QUERIES[key])

            if paths:
                params["inc"] = "+".join(paths)

        result = await self._http("/artist", params=params)

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
                recordings=[
                    MusicbrainzRecording(
                        id=recording.get("id", ""),
                        title=recording.get("title", ""),
                        length=recording.get("length"),
                        disambiguation=recording.get("disambiguation", ""),
                        video=recording.get("video", False),
                    )
                    for recording in artist.get("recordings", [])
                ],
            )
            for artist in result.get("artists", [])
        ]

    async def get_artist_alias(self, artist_name: str) -> str | None:
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

            await asyncio.sleep(self.SEARCH_POLL_INTERVAL)
        return None

    async def get_artist_info(
        self,
        artist_name: str,
    ) -> ArtistInfo | None:
        """Get artist metadata, optionally with related data."""
        try:
            artists = await self._get_artists(
                artist_name,
                options={"enableRecordings": True, "enableAliases": True},
            )

            if not artists:
                return None

            return artists[0].to_artist_info()
        except Exception as e:
            logger.error(
                f"Failed to fetch MusicBrainz artist info for '{artist_name}': {e}"
            )
            return None
