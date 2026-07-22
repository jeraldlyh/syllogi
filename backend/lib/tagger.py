import logging

from mutagen.flac import FLAC
from mutagen.id3 import ID3, TALB, TCON, TDRC, TIT2, TPE1, USLT
from mutagen.mp3 import MP3
from mutagen.oggopus import OggOpus

from lib.providers.lyrics.lrclib import LRCLIBLyricsProvider

logger = logging.getLogger(__name__)


def has_lyrics(file_path: str) -> bool:
    """Check if an audio file already has lyrics tagged."""

    try:
        if file_path.endswith(".flac"):
            audio = FLAC(file_path)
            return bool(audio.tags and audio.tags["LYRICS"])  # type: ignore[reportAttributeAccessIssue]
        elif file_path.endswith(".mp3"):
            audio = MP3(file_path)
            return bool(audio.tags and audio.tags.getall("USLT"))
        elif file_path.endswith(".opus"):
            audio = OggOpus(file_path)
            return bool(audio.tags and audio.tags["LYRICS"])  # type: ignore[reportAttributeAccessIssue]
        return False
    except Exception:
        return False


async def tag_audio_file(
    file_path: str,
    artist_name: str,
    track_name: str,
    album_name: str,
    year: str,
    genres: list[str],
    duration: int = 0,
) -> bool:
    """Write audio metadata tags to a downloaded file."""
    try:
        lyrics = ""

        if not has_lyrics(file_path):
            lrclib = LRCLIBLyricsProvider()
            lrc_lyrics = await lrclib.get_lyrics(
                artist_name=artist_name,
                track_name=track_name,
                album_name=album_name,
                duration=duration,
            )

            if lrc_lyrics:
                lyrics = lrc_lyrics

        if file_path.endswith(".flac"):
            _tag_flac(
                file_path=file_path,
                artist_name=artist_name,
                track_name=track_name,
                album_name=album_name,
                year=year,
                genres=genres,
                lyrics=lyrics,
            )
        elif file_path.endswith(".mp3"):
            _tag_mp3(
                file_path=file_path,
                artist_name=artist_name,
                track_name=track_name,
                album_name=album_name,
                year=year,
                genres=genres,
                lyrics=lyrics,
            )
        elif file_path.endswith(".opus"):
            _tag_opus(
                file_path=file_path,
                artist_name=artist_name,
                track_name=track_name,
                album_name=album_name,
                year=year,
                genres=genres,
                lyrics=lyrics,
            )
        else:
            logger.warning(f"Unsupported file format: {file_path}")
            return False

        logger.info(f"Tagged: {file_path}")
        return True
    except Exception:
        logger.error(f"Failed to tag: {file_path}")
        return False


def _tag_flac(
    file_path: str,
    artist_name: str,
    track_name: str,
    album_name: str,
    year: str,
    genres: list[str],
    lyrics: str,
) -> None:
    audio = FLAC(file_path)

    if not audio.tags:
        audio.add_tags()

    audio["TITLE"] = [track_name]
    audio["ARTIST"] = [artist_name]

    if album_name:
        audio["ALBUM"] = [album_name]

    if year:
        audio["DATE"] = [year]

    if genres:
        audio["GENRE"] = genres

    if lyrics:
        audio["LYRICS"] = [lyrics]

    audio.save()


def _tag_mp3(
    file_path: str,
    artist_name: str,
    track_name: str,
    album_name: str,
    year: str,
    genres: list[str],
    lyrics: str,
) -> None:
    audio = MP3(file_path)

    if not audio.tags:
        audio.add_tags()

    assert audio.tags is not None
    tags: ID3 = audio.tags

    tags.delall("TIT2")
    tags.add(TIT2(encoding=3, text=[track_name]))

    tags.delall("TPE1")
    tags.add(TPE1(encoding=3, text=[artist_name]))

    if album_name:
        tags.delall("TALB")
        tags.add(TALB(encoding=3, text=[album_name]))

    if year:
        tags.delall("TDRC")
        tags.add(TDRC(encoding=3, text=[year]))

    if genres:
        tags.delall("TCON")
        tags.add(TCON(encoding=3, text=genres))

    if lyrics:
        tags.delall("USLT")
        tags.add(USLT(encoding=3, lang="", desc="", text=lyrics))

    audio.save()


def _tag_opus(
    file_path: str,
    artist_name: str,
    track_name: str,
    album_name: str,
    year: str,
    genres: list[str],
    lyrics: str,
) -> None:
    audio = OggOpus(file_path)

    if not audio.tags:
        audio.add_tags()

    audio["TITLE"] = [track_name]
    audio["ARTIST"] = [artist_name]

    if album_name:
        audio["ALBUM"] = [album_name]

    if year:
        audio["DATE"] = [year]

    if genres:
        audio["GENRE"] = genres

    if lyrics:
        audio["LYRICS"] = [lyrics]

    audio.save()
