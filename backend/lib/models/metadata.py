from dataclasses import dataclass


@dataclass
class ArtistTrack:
    """A track by an artist."""

    artist_name: str
    track_name: str
    duration_ms: int | None
    disambiguation: str
    album_name: str
    genres: list[str]
    image_url: str

    async def ensure_metadata(self) -> None:
        """Ensure that metadata is set, by falling back to Deezer API"""

        from lib.providers.metadata.deezer import DeezerMetadataProvider

        deezer_provider = DeezerMetadataProvider()
        deezer_track = await deezer_provider.get_artist_recording(
            artist_name=self.artist_name,
            track_name=self.track_name,
        )

        if not deezer_track:
            return

        if not self.image_url and deezer_track.image_url:
            self.image_url = deezer_track.image_url

        if not self.album_name and deezer_track.album_name:
            self.album_name = deezer_track.album_name

    def get_duration(self) -> int:
        """Get the duration of the track in seconds."""

        if not self.duration_ms:
            return 0
        return self.duration_ms // 1000

    def to_dict(self, exists: bool) -> dict[str, str | int | bool | list]:
        """Convert the ArtistTrack to a dictionary representation."""

        return {
            "track_name": self.track_name,
            "duration": self.get_duration(),
            "disambiguation": self.disambiguation,
            "album_name": self.album_name,
            "genres": self.genres,
            "image_url": self.image_url,
            "exists": exists,
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
