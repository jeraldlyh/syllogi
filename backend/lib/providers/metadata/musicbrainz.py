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
from lib.models.metadata import AlbumInfo, ArtistTrack
from lib.cache import cached_method
from lib.providers.metadata.base import (
    ArtistInfo,
    MetadataProvider,
)

logger = logging.getLogger(__name__)


class MusicBrainzMetadataProvider(MetadataProvider):
    """Metadata provider backed by the MusicBrainz API."""

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

    @cached_method(ttl=604800)
    async def get_artist_tracks(
        self,
        *,
        artist_mbid: str,
        limit: int,
    ) -> list[ArtistTrack]:
        """Fetch tracks by artist MusicBrainz ID."""

        result = await self._http(
            f"/artist/{artist_mbid}",
            params={"inc": "recordings+genres", "limit": limit},
        )

        if not result:
            return []

        unique = set()
        for track in result.get("recordings", []):
            if not track.get("length") or track.get("length") == 0:
                continue

            unique.add(
                ArtistTrack(
                    artist_name=result.get("name", ""),
                    track_name=track.get("title", ""),
                    duration_ms=track.get("length"),
                    disambiguation=track.get("disambiguation", ""),
                    album_name="",
                    genres=[genre.get("name") for genre in track.get("genres", [])],
                    image_url="",
                )
            )
        return list(unique)

    @cached_method(ttl=604800)
    async def get_artist_track(
        self,
        *,
        artist_name: str,
        track_name: str,
    ) -> ArtistTrack | None:
        """Search MusicBrainz for a track by artist and track name."""

        query = f'recording:"{track_name}" AND artist:"{artist_name}"'
        result = await self._http(
            "/recording",
            params={"query": query, "inc": "genres", "limit": 1},
        )

        if not result or not result.get("recordings"):
            return

        track = result.get("recordings")[0]
        releases = track.get("releases", [])
        release_group = releases[0].get("release-group", {}) if releases else {}

        return ArtistTrack(
            artist_name=artist_name,
            track_name=track.get("title", ""),
            duration_ms=track.get("length"),
            disambiguation=track.get("disambiguation", ""),
            album_name=release_group.get("title", ""),
            genres=[genre.get("name") for genre in track.get("genres", [])],
            image_url="",
        )

    @cached_method(ttl=604800)
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

    @cached_method(ttl=604800)
    async def get_album_info(
        self,
        *,
        artist_name: str,
        album_name: str,
    ) -> AlbumInfo | None:
        """Search MusicBrainz for a release group and return its metadata with tracks."""

        query = f'release-group:"{album_name}" AND artist:"{artist_name}"'
        result = await self._http(
            "/release-group",
            params={"query": query, "limit": 1},
        )

        if not result or not result.get("release-groups"):
            return None

        release_group = result["release-groups"][0]
        releases = release_group.get("releases", [])

        if not releases:
            return None

        release = releases[0]
        release_id = release.get("id")

        release_detail = await self._http(
            f"/release/{release_id}",
            params={"inc": "recordings"},
        )

        if not release_detail:
            return None

        tracks: list[ArtistTrack] = []
        release_media = release_detail.get("media", [])

        if not release_media:
            return None

        for track in release_media[0].get("tracks", []):
            recording = track.get("recording", {})

            tracks.append(
                ArtistTrack(
                    artist_name=artist_name,
                    track_name=recording.get("title", track.get("title", "")),
                    duration_ms=recording.get("length", 0),
                    disambiguation=recording.get("disambiguation", ""),
                    album_name=album_name,
                    genres=[],
                    image_url="",
                )
            )

        return AlbumInfo(
            album_name=release_group.get("title", album_name),
            artist_name=artist_name,
            image_url="",
            release_date=release_group.get("first-release-date", ""),
            tracks=tracks,
        )

    @cached_method(ttl=604800)
    async def get_artist_alias(self, *, artist_name: str) -> str | None:
        """Get artist actual name using MusicBrainz.

        This is useful for artists with non-Latin names, but has an English name as an alias.

        For example, Spotify returns "Joker Xue" as an alias for "薛之谦".
        """

        artists = await self._get_artists(artist_name=artist_name)

        if artists:
            return artists[0].name
        return None
