import logging
import os
import re
import unicodedata

from mutagen import MutagenError
from mutagen.flac import FLAC
from mutagen.id3 import ID3, TALB, TCON, TDRC, TIT2, TPE1, UFID, USLT
from mutagen.mp3 import MP3
from mutagen.oggopus import OggOpus

from lib.models.library import AudioTags
from lib.providers.lyrics.lrclib import LRCLIBLyricsProvider

logger = logging.getLogger(__name__)


LRC_TIMESTAMP = re.compile(r"(?:\[\d{1,3}:\d{2}(?:[.:]\d{1,3})?\]\s*)+")
LRC_LINE_TIMESTAMP = re.compile(r"^\[\d{1,3}:\d{2}(?:[.:]\d{1,3})?\]")
MUSICBRAINZ_UFID_OWNER = "http://musicbrainz.org"
SUPPORTED_EXTENSIONS = (".flac", ".mp3", ".opus")
VORBIS_FRAMES = {
    "title": "TITLE",
    "artist": "ARTIST",
    "album": "ALBUM",
    "date": "DATE",
    "genres": "GENRE",
    "lyrics": "LYRICS",
    "musicbrainz_id": "MUSICBRAINZ_TRACKID",
}
ID3_FRAMES = {
    "title": "TIT2",
    "artist": "TPE1",
    "album": "TALB",
    "date": "TDRC",
    "genres": "TCON",
    "lyrics": "USLT",
    "musicbrainz_id": "UFID",
}


def resolve_existing_path(file_path: str) -> str:
    """Returns the path that exists on disk, normalizing Unicode if necessary."""

    if os.path.exists(file_path):
        return file_path

    for form in ("NFC", "NFD"):
        candidate = unicodedata.normalize(form, file_path)

        if candidate != file_path and os.path.exists(candidate):
            return candidate
    return file_path


def get_extension(file_path: str) -> str:
    """Return the lowercased file extension."""

    return os.path.splitext(file_path)[1].lower()


def is_synced_lyrics(text: str) -> bool:
    """Check whether the lyrics carry LRC timestamps."""

    if not text:
        return False

    return any(LRC_LINE_TIMESTAMP.match(line.strip()) for line in text.splitlines())


def get_tag_frames(file_path: str) -> dict[str, str]:
    """Return the container's tag name for each editable field.

    FLAC and Opus store Vorbis comments; MP3 stores ID3v2 frames.
    """

    if get_extension(file_path) == ".mp3":
        return dict(ID3_FRAMES)
    return dict(VORBIS_FRAMES)


def get_lyrics_tag(tags) -> str | None:
    """Extract the LYRICS value from a mutagen Vorbis-style tag dict."""
    if tags is None:
        return None

    value = tags.get("LYRICS")

    if isinstance(value, (list, tuple)):
        return "\n".join(str(part) for part in value)
    return value if isinstance(value, str) else None


def is_valid_lyrics(text: str | None) -> bool:
    """Verifies if the text contains meaningful lyrics content."""
    if not text or not text.strip():
        return False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if LRC_TIMESTAMP.fullmatch(stripped):
            continue
        return True

    return False


def _get_first_value(value) -> str:
    """Read the first entry of a mutagen tag value, which may be a list or a scalar."""

    if value is None:
        return ""

    if isinstance(value, (list, tuple)):
        return str(value[0]) if value else ""
    return str(value)


def _read_vorbis_tags(tags) -> AudioTags:
    """Read editable tags from a Vorbis comment block (FLAC and Opus)."""

    if tags is None:
        return AudioTags()

    return AudioTags(
        title=_get_first_value(tags.get("TITLE")),
        artist=_get_first_value(tags.get("ARTIST")),
        album=_get_first_value(tags.get("ALBUM")),
        date=_get_first_value(tags.get("DATE")),
        genres=[str(genre) for genre in (tags.get("GENRE") or [])],
        lyrics=get_lyrics_tag(tags) or "",
        musicbrainz_id=_get_first_value(tags.get("MUSICBRAINZ_TRACKID")),
    )


def _read_id3_tags(tags: ID3 | None) -> AudioTags:
    """Read editable tags from an ID3v2 tag block (MP3)."""

    if tags is None:
        return AudioTags()

    def text(frame_id: str) -> str:
        frame = tags.get(frame_id)
        return str(frame.text[0]) if frame and frame.text else ""

    genre_frame = tags.get("TCON")
    genres = [str(genre) for genre in genre_frame.text] if genre_frame else []

    lyrics = ""
    for frame in tags.getall("USLT"):
        if frame.text:
            lyrics = str(frame.text)
            break

    musicbrainz_id = ""
    for frame in tags.getall("UFID"):
        if frame.owner == MUSICBRAINZ_UFID_OWNER:
            musicbrainz_id = frame.data.decode("utf-8", errors="ignore")
            break

    if not musicbrainz_id:
        for frame in tags.getall("TXXX"):
            if frame.desc == "MusicBrainz Track Id" and frame.text:
                musicbrainz_id = str(frame.text[0])
                break

    return AudioTags(
        title=text("TIT2"),
        artist=text("TPE1"),
        album=text("TALB"),
        date=text("TDRC"),
        genres=genres,
        lyrics=lyrics,
        musicbrainz_id=musicbrainz_id,
    )


def read_audio_tags(file_path: str) -> tuple[AudioTags, int] | None:
    """Read the editable tags and duration of an audio file.

    Returns a tuple of (tags, duration in seconds), or None if the file cannot be read.
    """

    try:
        readable_path = resolve_existing_path(file_path)
        extension = get_extension(file_path)

        if extension == ".flac":
            audio = FLAC(readable_path)
            tags = _read_vorbis_tags(audio.tags)
        elif extension == ".opus":
            audio = OggOpus(readable_path)
            tags = _read_vorbis_tags(audio.tags)
        elif extension == ".mp3":
            audio = MP3(readable_path)
            tags = _read_id3_tags(audio.tags)
        else:
            return None

        duration = int(audio.info.length) if audio.info else 0

        return tags, duration
    except (MutagenError, OSError, KeyError, ValueError):
        logger.warning(f"Failed to read tags: {file_path}")
        return None


def _write_vorbis_tags(audio, tags: AudioTags) -> None:
    """Write the full editable tag set to a Vorbis comment block, clearing empty fields."""

    if audio.tags is None:
        audio.add_tags()

    values = {
        "TITLE": [tags.title] if tags.title else [],
        "ARTIST": [tags.artist] if tags.artist else [],
        "ALBUM": [tags.album] if tags.album else [],
        "DATE": [tags.date] if tags.date else [],
        "GENRE": tags.genres,
        "LYRICS": [tags.lyrics] if tags.lyrics else [],
        "MUSICBRAINZ_TRACKID": [tags.musicbrainz_id] if tags.musicbrainz_id else [],
    }

    for key, value in values.items():
        if value:
            audio[key] = value
        elif key in audio:
            del audio[key]

    audio.save()


def _write_id3_tags(audio: MP3, tags: AudioTags) -> None:
    """Write the full editable tag set to an ID3v2 tag block, clearing empty fields."""

    if audio.tags is None:
        audio.add_tags()

    assert audio.tags is not None
    id3: ID3 = audio.tags

    frames = {
        "TIT2": TIT2(encoding=3, text=[tags.title]) if tags.title else None,
        "TPE1": TPE1(encoding=3, text=[tags.artist]) if tags.artist else None,
        "TALB": TALB(encoding=3, text=[tags.album]) if tags.album else None,
        "TDRC": TDRC(encoding=3, text=[tags.date]) if tags.date else None,
        "TCON": TCON(encoding=3, text=tags.genres) if tags.genres else None,
        "USLT": USLT(encoding=3, lang="und", desc="", text=tags.lyrics)
        if tags.lyrics
        else None,
    }

    for frame_id, frame in frames.items():
        id3.delall(frame_id)

        if frame is not None:
            id3.add(frame)

    id3.pop(f"UFID:{MUSICBRAINZ_UFID_OWNER}", None)
    id3.delall("TXXX:MusicBrainz Track Id")

    if tags.musicbrainz_id:
        id3.add(
            UFID(
                owner=MUSICBRAINZ_UFID_OWNER,
                data=tags.musicbrainz_id.encode("utf-8"),
            )
        )

    audio.save()


def write_audio_tags(file_path: str, tags: AudioTags) -> None:
    """Write the full editable tag set to an audio file.

    Every field is written, so a field submitted empty clears the tag on disk.

    Raises:
        ValueError: If the file format is not supported.
        MutagenError, OSError: If the file cannot be written.
    """

    writable_path = resolve_existing_path(file_path)
    extension = get_extension(file_path)

    if extension == ".flac":
        _write_vorbis_tags(FLAC(writable_path), tags)
    elif extension == ".opus":
        _write_vorbis_tags(OggOpus(writable_path), tags)
    elif extension == ".mp3":
        _write_id3_tags(MP3(writable_path), tags)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")

    logger.info(f"Wrote tags: {file_path}")


async def tag_audio_file(
    file_path: str,
    artist_name: str,
    track_name: str,
    album_name: str,
    year: str,
    genres: list[str],
    duration: int = 0,
) -> bool:
    """Write metadata to a freshly downloaded file, fetching lyrics if it has none."""

    existing = read_audio_tags(file_path)

    if existing is None:
        logger.warning(f"Unable to tag unsupported or unreadable file: {file_path}")
        return False

    current, _ = existing
    lyrics = current.lyrics

    if not is_valid_lyrics(lyrics):
        provider = LRCLIBLyricsProvider()
        candidates = await provider.search_lyrics(
            artist_name=artist_name,
            track_name=track_name,
            album_name=album_name,
        )
        lyrics = provider.select_lyrics(candidates=candidates, duration=duration)

    try:
        write_audio_tags(
            file_path=file_path,
            tags=AudioTags(
                title=track_name or current.title,
                artist=artist_name or current.artist,
                album=album_name or current.album,
                date=year or current.date,
                genres=genres or current.genres,
                lyrics=lyrics,
                musicbrainz_id=current.musicbrainz_id,
            ),
        )
    except (MutagenError, OSError, ValueError):
        logger.error(f"Failed to tag: {file_path}")
        return False
    return True
