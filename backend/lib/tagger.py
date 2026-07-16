import logging

from mutagen.flac import FLAC
from mutagen.id3 import ID3, TALB, TCON, TDRC, TIT2, TPE1
from mutagen.mp3 import MP3
from mutagen.oggopus import OggOpus

logger = logging.getLogger(__name__)


def tag_audio_file(
    file_path: str,
    artist_name: str,
    track_name: str,
    album_name: str,
    year: str,
    genres: list[str],
) -> bool:
    """Write audio metadata tags to a downloaded file."""
    try:
        if file_path.endswith(".flac"):
            _tag_flac(
                file_path=file_path,
                artist_name=artist_name,
                track_name=track_name,
                album_name=album_name,
                year=year,
                genres=genres,
            )
        elif file_path.endswith(".mp3"):
            _tag_mp3(
                file_path=file_path,
                artist_name=artist_name,
                track_name=track_name,
                album_name=album_name,
                year=year,
                genres=genres,
            )
        elif file_path.endswith(".opus"):
            _tag_opus(
                file_path=file_path,
                artist_name=artist_name,
                track_name=track_name,
                album_name=album_name,
                year=year,
                genres=genres,
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

    audio.save()


def _tag_mp3(
    file_path: str,
    artist_name: str,
    track_name: str,
    album_name: str,
    year: str,
    genres: list[str],
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

    audio.save()


def _tag_opus(
    file_path: str,
    artist_name: str,
    track_name: str,
    album_name: str,
    year: str,
    genres: list[str],
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

    audio.save()
