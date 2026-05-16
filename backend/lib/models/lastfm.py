from dataclasses import dataclass

from lib.models.common import ExternalTrack


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

    def __eq__(self, other) -> bool:
        return (
            self.artist_name == other.artist_name
            and self.track_name == other.track_name
            and self.musicbrainz_id == other.musicbrainz_id
        )

    def __hash__(self) -> int:
        return (
            hash(self.artist_name) + hash(self.track_name) + hash(self.musicbrainz_id)
        )

    def to_dict(self) -> dict[str, str | int]:
        return {
            "artist_name": self.artist_name,
            "track_name": self.track_name,
            "album_name": self.album_name,
            "musicbrainz_id": self.musicbrainz_id,
            "type": "recent",
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

    def __eq__(self, other) -> bool:
        return (
            self.artist_name == other.artist_name
            and self.track_name == other.track_name
            and self.musicbrainz_id == other.musicbrainz_id
        )

    def __hash__(self) -> int:
        return (
            hash(self.artist_name) + hash(self.track_name) + hash(self.musicbrainz_id)
        )

    def to_dict(self) -> dict[str, str | int]:
        return {
            "artist_name": self.artist_name,
            "track_name": self.track_name,
            "duration": self.duration,
            "musicbrainz_id": self.musicbrainz_id,
            "playcount": self.playcount,
            "type": "top",
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

    def __eq__(self, other) -> bool:
        return (
            self.artist_name == other.artist_name
            and self.track_name == other.track_name
            and self.musicbrainz_id == other.musicbrainz_id
        )

    def __hash__(self) -> int:
        return (
            hash(self.artist_name) + hash(self.track_name) + hash(self.musicbrainz_id)
        )

    def to_dict(self) -> dict[str, str | int | float]:
        return {
            "artist_name": self.artist_name,
            "track_name": self.track_name,
            "duration": self.duration,
            "musicbrainz_id": self.musicbrainz_id,
            "playcount": self.playcount,
            "similarity_score": self.similarity_score,
            "type": "similar",
        }

    def to_external_track(self) -> ExternalTrack:
        return ExternalTrack(
            artist_name=self.artist_name,
            track_name=self.track_name,
            album_name="",
            year="",
            duration=self.duration,
        )
