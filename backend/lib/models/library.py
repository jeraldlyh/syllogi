from dataclasses import dataclass, field


@dataclass
class AudioTags:
    """Editable metadata tags read from, or written to, an audio file."""

    title: str = ""
    artist: str = ""
    album: str = ""
    date: str = ""
    genres: list[str] = field(default_factory=list)
    lyrics: str = ""
    musicbrainz_id: str = ""

    def to_dict(self) -> dict:
        """Convert the AudioTags to a dictionary representation."""

        return {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "date": self.date,
            "genres": self.genres,
            "lyrics": self.lyrics,
            "musicbrainz_id": self.musicbrainz_id,
        }


@dataclass
class LyricsCandidate:
    """A lyrics match returned by LRCLIB."""

    id: int
    track_name: str
    artist_name: str
    album_name: str
    duration: int
    instrumental: bool
    plain_lyrics: str
    synced_lyrics: str

    def to_dict(self) -> dict:
        """Convert the LyricsCandidate to a dictionary representation."""

        return {
            "id": self.id,
            "track_name": self.track_name,
            "artist_name": self.artist_name,
            "album_name": self.album_name,
            "duration": self.duration,
            "instrumental": self.instrumental,
            "plain_lyrics": self.plain_lyrics,
            "synced_lyrics": self.synced_lyrics,
        }
