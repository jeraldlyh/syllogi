from dataclasses import dataclass, field

LRC_LINE_PREFIX = "["


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
class LibraryTrack:
    """An audio file in the download library, with the tags it currently carries."""

    path: str
    filename: str
    directory: str
    format: str
    size: int
    duration: int
    tags: AudioTags
    has_lyrics: bool

    def is_synced_lyrics(self) -> bool:
        """Check whether the lyrics on this file carry LRC timestamps."""

        return any(
            line.strip().startswith(LRC_LINE_PREFIX)
            for line in self.tags.lyrics.splitlines()
        )

    def filled_fields(self) -> list[str]:
        """List the tag fields that carry a value on this file."""

        filled = []

        if self.tags.title:
            filled.append("title")
        if self.tags.artist:
            filled.append("artist")
        if self.tags.album:
            filled.append("album")
        if self.tags.date:
            filled.append("date")
        if self.tags.genres:
            filled.append("genres")
        if self.has_lyrics:
            filled.append("lyrics")
        if self.tags.musicbrainz_id:
            filled.append("musicbrainz_id")
        return filled

    def to_dict(self, include_lyrics: bool = False) -> dict:
        """Convert the LibraryTrack to a dictionary representation.

        Lyrics bodies are omitted from list responses, which would otherwise carry
        the full text of every file in the library.
        """

        tags = self.tags.to_dict()

        if not include_lyrics:
            tags.pop("lyrics")

        return {
            "path": self.path,
            "filename": self.filename,
            "directory": self.directory,
            "format": self.format,
            "size": self.size,
            "duration": self.duration,
            "has_lyrics": self.has_lyrics,
            "is_synced_lyrics": self.is_synced_lyrics(),
            "filled_fields": self.filled_fields(),
            "tags": tags,
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
