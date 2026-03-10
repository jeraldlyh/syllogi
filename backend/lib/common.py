from dataclasses import dataclass, field


@dataclass
class Track:
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
class ExternalPlaylist:
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
    """A source song that has been resolved against the Jellyfin library."""

    track: Track
    jellyfin_id: str | None = None
    display_name: str = ""


@dataclass
class PlaylistDiff:
    """Result of diffing resolved source tracks against an existing Jellyfin playlist."""

    added: list[ResolvedTrack] = field(default_factory=list)
    removed: list[dict] = field(default_factory=list)
    unchanged: list[ResolvedTrack] = field(default_factory=list)
