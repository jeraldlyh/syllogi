import asyncio
from dataclasses import dataclass


@dataclass
class ArtistTrack:
    """A track by an artist.

    The trailing fields are only populated by providers that expose them (today
    MusicBrainz); they carry everything needed to retag a file. Providers that
    cannot supply them leave them at their defaults.
    """

    artist_name: str
    track_name: str
    duration_ms: int | None
    disambiguation: str
    album_name: str
    genres: list[str]
    image_url: str
    id: str = ""
    release_date: str = ""
    score: int = 0

    async def ensure_metadata(self) -> None:
        """Ensure that metadata is set, by falling back to Deezer API"""

        from lib.providers.metadata.deezer import DeezerMetadataProvider

        deezer_provider = DeezerMetadataProvider()
        deezer_track = await deezer_provider.get_artist_track(
            artist_name=self.artist_name,
            track_name=self.track_name,
        )

        if deezer_track:
            if not self.image_url and deezer_track.image_url:
                self.image_url = deezer_track.image_url

            if not self.album_name and deezer_track.album_name:
                self.album_name = deezer_track.album_name

        if not self.image_url:
            deezer_artist = await deezer_provider.get_artist_info(
                artist_name=self.artist_name,
            )
            if deezer_artist and deezer_artist.image_url:
                self.image_url = deezer_artist.image_url

    def get_duration(self) -> int:
        """Get the duration of the track in seconds."""

        if not self.duration_ms:
            return 0
        return self.duration_ms // 1000

    def get_year(self) -> str:
        """Get the release year, from a date that may be a year, year-month or full date."""

        if not self.release_date:
            return ""
        return self.release_date.split("-")[0]

    def to_search_dict(self) -> dict[str, str | int | list]:
        """Convert the ArtistTrack to a search-result dictionary representation.

        Unlike `to_dict`, this is synchronous and does no provider lookup, so it
        is safe to call for every hit in a result set.
        """

        return {
            "id": self.id,
            "title": self.track_name,
            "artist_name": self.artist_name,
            "album_name": self.album_name,
            "release_date": self.release_date,
            "year": self.get_year(),
            "duration": self.get_duration(),
            "disambiguation": self.disambiguation,
            "genres": self.genres,
            "score": self.score,
        }

    async def to_dict(
        self,
    ) -> dict[str, str | int | bool | list]:
        """Convert the ArtistTrack to a dictionary representation."""

        from lib.providers import get_provider
        from lib.track import find_track

        provider = get_provider()
        provider_track = await find_track(
            provider=provider,
            artist_name=self.artist_name,
            track_name=self.track_name,
            album_name=self.album_name,
            year="",
            duration=self.get_duration(),
        )

        return {
            "track_name": self.track_name,
            "duration": self.get_duration(),
            "disambiguation": self.disambiguation,
            "album_name": self.album_name,
            "genres": self.genres,
            "image_url": self.image_url,
            "exists": not provider_track.is_not_found(),
        }

    def __eq__(self, other):
        """Check equality based on track name, case-insensitive."""

        if not isinstance(other, ArtistTrack):
            return NotImplemented
        return self.track_name.casefold() == other.track_name.casefold()

    def __hash__(self):
        """Hash based on track name, case-insensitive."""

        return hash(self.track_name.casefold())


@dataclass
class ArtistInfo:
    """Full artist metadata, including optional related data."""

    MAX_ALIASES = 5

    id: str
    name: str
    type: str
    country: str
    gender: str
    life_span: dict[str, str | None]
    area: str | None
    begin_area: str | None
    tags: list[str]
    aliases: list[str]
    image_url: str | None = None
    num_of_fans: int | None = None

    async def ensure_metadata(self) -> None:
        """Ensure that metadata is set, by falling back to Deezer API"""

        from lib.providers.metadata.deezer import DeezerMetadataProvider

        if self.image_url is not None and self.num_of_fans is not None:
            return

        deezer_provider = DeezerMetadataProvider()
        deezer_artist = await deezer_provider.get_artist_info(artist_name=self.name)

        if not deezer_artist:
            return

        if deezer_artist.image_url is not None:
            self.image_url = deezer_artist.image_url

        if deezer_artist.num_of_fans is not None:
            self.num_of_fans = deezer_artist.num_of_fans

    def to_dict(self) -> dict[str, str | dict | list | int | None]:
        """Convert the ArtistInfo to a dictionary representation."""

        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "country": self.country,
            "gender": self.gender,
            "life_span": self.life_span,
            "area": self.area,
            "begin_area": self.begin_area,
            "tags": self.tags,
            "aliases": self.aliases[: self.MAX_ALIASES],
            "image_url": self.image_url,
            "num_of_fans": self.num_of_fans,
        }


@dataclass
class AlbumInfo:
    """Album metadata with tracklist."""

    album_name: str
    artist_name: str
    image_url: str
    release_date: str
    tracks: list[ArtistTrack]

    async def ensure_metadata(self) -> None:
        from lib.providers.metadata.deezer import DeezerMetadataProvider

        if self.image_url:
            return

        deezer_provider = DeezerMetadataProvider()
        deezer_album = await deezer_provider.get_album_info(
            artist_name=self.artist_name,
            album_name=self.album_name,
            exclude_tracks=True,
        )

        if not deezer_album:
            return
        self.image_url = deezer_album.image_url

    async def to_dict(self) -> dict[str, str | int | list[dict]]:
        await asyncio.gather(*[track.ensure_metadata() for track in self.tracks])

        return {
            "title": self.album_name,
            "artist_name": self.artist_name,
            "image_url": self.image_url,
            "release_date": self.release_date,
            "tracks": [await track.to_dict() for track in self.tracks],
        }
