from dataclasses import dataclass, field

from lib.models.provider import ProviderTrack


@dataclass
class ExternalTrack:
    """A source track from an external service (Spotify/Youtube)."""

    def __init__(
        self,
        artist_name: str,
        track_name: str,
        album_name: str = "",
        year: str = "",
        duration: int = 0,
    ):
        self.artist_name = artist_name
        self.track_name = track_name
        self.album_name = album_name
        self.year = year
        self.duration = duration

    def to_dict(self) -> dict[str, str | int]:
        return {
            "artist_name": self.artist_name,
            "track_name": self.track_name,
            "album_name": self.album_name,
            "year": self.year,
            "duration": self.duration,
        }


@dataclass
class ExternalSync:
    """A source playlist from an external service (Spotify/Youtube)."""

    def __init__(
        self,
        id: str,
        name: str,
        thumbnail_url: str,
        total: int,
    ):
        self.id = id
        self.name = name
        self.thumbnail_url = thumbnail_url
        self.total = total

    def to_dict(self) -> dict[str, str | int]:
        return {
            "id": self.id,
            "name": self.name,
            "thumbnail_url": self.thumbnail_url,
            "total": self.total,
        }


@dataclass
class ResolvedTrack:
    """A source song that has been resolved against the music provider library."""

    track: ExternalTrack
    provider_track_id: str | None = None
    display_name: str = ""
    jellyfin_id: str | None = None


@dataclass
class SyncDiff:
    """Result of diffing resolved source tracks against an existing provider playlist."""

    added: list[ResolvedTrack] = field(default_factory=list)
    removed: list[ProviderTrack] = field(default_factory=list)
    unchanged: list[ResolvedTrack] = field(default_factory=list)
