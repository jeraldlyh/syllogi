from dataclasses import dataclass, field


class ProviderError(Exception):
    """Raised when a music provider operation fails."""

    pass


@dataclass
class ProviderUser:
    """A user in a music server."""

    id: str = ""
    name: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "name": self.name}


@dataclass
class ProviderTrack:
    """A track in a music server."""

    id: str = ""
    track_name: str = ""
    album_name: str = ""
    album_id: str = ""
    musicbrainz_id: str = ""
    artists: list[str] = field(default_factory=list)
    duration_ticks: int = 0
    year: str = ""

    def is_not_found(self) -> bool:
        return not self.id

    def to_dict(self) -> dict[str, str | int | list[str]]:
        return {
            "id": self.id,
            "track_name": self.track_name,
            "album_name": self.album_name,
            "album_id": self.album_id,
            "musicbrainz_id": self.musicbrainz_id,
            "artists": self.artists,
            "duration_ticks": self.duration_ticks,
            "year": self.year,
        }


@dataclass
class ProviderPlaylist:
    """A playlist in a music server."""

    id: str = ""
    name: str = ""
    owner_id: str | None = None

    def to_dict(self) -> dict[str, str | int | None]:
        return {"id": self.id, "name": self.name, "owner_id": self.owner_id}
