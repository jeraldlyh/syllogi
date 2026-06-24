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


@dataclass
class SyncDiff:
    """Result of diffing resolved source tracks against an existing provider playlist."""

    added: list[ResolvedTrack] = field(default_factory=list)
    removed: list[ProviderTrack] = field(default_factory=list)
    unchanged: list[ResolvedTrack] = field(default_factory=list)


@dataclass
class RecommendationTrack:
    """A track returned by a recommendation source provider."""

    artist_name: str
    track_name: str
    musicbrainz_id: str
    album_name: str
    duration: int
    playcount: int
    similarity_score: float

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RecommendationTrack):
            return NotImplemented

        return (
            self.artist_name == other.artist_name
            and self.track_name == other.track_name
            and self.musicbrainz_id == other.musicbrainz_id
        )

    def __hash__(self) -> int:
        return hash((self.artist_name, self.track_name, self.musicbrainz_id))

    def to_external_track(self) -> ExternalTrack:
        """Convert this recommendation track to an ExternalTrack instance."""
        return ExternalTrack(
            artist_name=self.artist_name,
            track_name=self.track_name,
            album_name=self.album_name,
            duration=self.duration,
        )
