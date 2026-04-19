from dataclasses import dataclass, field


@dataclass
class JellyfinUser:
    """A user in Jellyfin."""

    def __init__(
        self,
        id: str,
        name: str,
    ):
        self.id = id
        self.name = name

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "name": self.name,
        }


@dataclass
class JellyfinTrack:
    """A track in Jellyfin."""

    def __init__(
        self,
        id: str,
        track_name: str,
        album_name: str,
        album_id: str,
        musicbrainz_id: str,
        artists: list[str],
        duration_ticks: int,
        year: str,
    ):
        self.id = id
        self.track_name = track_name
        self.album_name = album_name
        self.album_id = album_id
        self.musicbrainz_id = musicbrainz_id
        self.artists = artists
        self.duration_ticks = duration_ticks
        self.year = year

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
class JellyfinPlaylist:
    """A playlist in Jellyfin."""

    def __init__(
        self,
        id: str,
        name: str,
    ):
        self.id = id
        self.name = name

    def to_dict(self) -> dict[str, str | int]:
        return {
            "id": self.id,
            "name": self.name,
        }


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
class ExternalPlaylist:
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
    """A source song that has been resolved against the Jellyfin library."""

    track: ExternalTrack
    jellyfin_id: str | None = None
    display_name: str = ""


@dataclass
class PlaylistDiff:
    """Result of diffing resolved source tracks against an existing Jellyfin playlist."""

    added: list[ResolvedTrack] = field(default_factory=list)
    removed: list[JellyfinTrack] = field(default_factory=list)
    unchanged: list[ResolvedTrack] = field(default_factory=list)


@dataclass
class LastFMRecentTrack:
    """A recently played track from LastFM."""

    def __init__(
        self,
        artist_name: str,
        track_name: str,
        album_name: str,
        musicbrainz_id: str,
    ):
        self.artist_name = artist_name
        self.track_name = track_name
        self.album_name = album_name
        self.musicbrainz_id = musicbrainz_id

    def to_dict(self) -> dict[str, str | int]:
        return {
            "artist_name": self.artist_name,
            "track_name": self.track_name,
            "album_name": self.album_name,
            "musicbrainz_id": self.musicbrainz_id,
        }


@dataclass
class LastFMTopTrack:
    """A top track from LastFM."""

    def __init__(
        self,
        artist_name: str,
        track_name: str,
        duration: int,
        musicbrainz_id: str,
        playcount: int,
    ):
        self.artist_name = artist_name
        self.track_name = track_name
        self.duration = duration
        self.musicbrainz_id = musicbrainz_id
        self.playcount = playcount

    def to_dict(self) -> dict[str, str | int]:
        return {
            "artist_name": self.artist_name,
            "track_name": self.track_name,
            "duration": self.duration,
            "musicbrainz_id": self.musicbrainz_id,
            "playcount": self.playcount,
        }


@dataclass
class LastFMSimilarTrack:
    """A similar track from LastFM."""

    def __init__(
        self,
        artist_name: str,
        track_name: str,
        duration: int,
        musicbrainz_id: str,
        playcount: int,
        similarity_score: float,
    ):
        self.artist_name = artist_name
        self.track_name = track_name
        self.duration = duration
        self.musicbrainz_id = musicbrainz_id
        self.playcount = playcount
        self.similarity_score = similarity_score

    def to_dict(self) -> dict[str, str | int | float]:
        return {
            "artist_name": self.artist_name,
            "track_name": self.track_name,
            "duration": self.duration,
            "musicbrainz_id": self.musicbrainz_id,
            "playcount": self.playcount,
            "similarity_score": self.similarity_score,
        }
