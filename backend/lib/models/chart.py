from dataclasses import dataclass


@dataclass
class ChartTrendingTrack:
    """A globally trending chart track."""

    def __init__(
        self,
        artist_name: str,
        track_name: str,
        album_name: str,
        duration: int,
        listeners: int,
        playcount: int,
        musicbrainz_id: str,
        image_url: str,
    ):
        self.artist_name = artist_name
        self.track_name = track_name
        self.album_name = album_name
        self.duration = duration
        self.listeners = listeners
        self.playcount = playcount
        self.musicbrainz_id = musicbrainz_id
        self.image_url = image_url

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ChartTrendingTrack):
            return NotImplemented

        return (
            self.artist_name == other.artist_name
            and self.track_name == other.track_name
            and self.musicbrainz_id == other.musicbrainz_id
        )

    def __hash__(self) -> int:
        return hash((self.artist_name, self.track_name, self.musicbrainz_id))

    def to_dict(self) -> dict[str, str | int]:
        return {
            "artist_name": self.artist_name,
            "track_name": self.track_name,
            "album_name": self.album_name,
            "duration": self.duration,
            "listeners": self.listeners,
            "playcount": self.playcount,
            "musicbrainz_id": self.musicbrainz_id,
            "image_url": self.image_url,
        }
