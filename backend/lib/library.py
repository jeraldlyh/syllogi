import logging
import os
import threading
import time
from pathlib import Path

from fastapi import HTTPException, status

from lib.env import get_environment_variable
from lib.models.library import LibraryTrack
from lib.tagger import (
    SUPPORTED_EXTENSIONS,
    is_valid_lyrics,
    read_audio_tags,
)
from lib.utils import normalize

logger = logging.getLogger(__name__)

SCAN_CACHE_TTL = 60.0

_track_cache: dict[str, tuple[float, LibraryTrack]] = {}
_scan_cache: tuple[float, list[LibraryTrack], list[str]] | None = None
_scan_lock = threading.Lock()


def get_library_directory() -> Path:
    """Return the resolved root directory holding the downloaded audio files."""

    return Path(str(get_environment_variable("DOWNLOAD_DIR"))).resolve()


def resolve_library_path(path: str) -> Path:
    """Resolve a library-relative path to an audio file on disk.

    Raises:
        HTTPException: If the path escapes the library, is not an audio file, or is missing.
    """

    library_directory = get_library_directory()
    resolved = Path(os.path.realpath(library_directory / path))

    if resolved != library_directory and library_directory not in resolved.parents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path is outside the library directory",
        )

    if resolved.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: {resolved.suffix or resolved.name}",
        )

    if not resolved.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No file found at {path}",
        )

    return resolved


def read_library_track(file_path: Path) -> LibraryTrack | None:
    """Read a single audio file into a LibraryTrack, or None if its tags cannot be read."""

    library_directory = get_library_directory()

    try:
        stat = file_path.stat()
    except OSError:
        return None

    relative_path = str(file_path.relative_to(library_directory))
    cached = _track_cache.get(relative_path)

    if cached and cached[0] == stat.st_mtime:
        return cached[1]

    result = read_audio_tags(str(file_path))

    if result is None:
        return None

    tags, duration = result
    directory = str(file_path.parent.relative_to(library_directory))

    track = LibraryTrack(
        path=relative_path,
        filename=file_path.name,
        directory="" if directory == "." else directory,
        format=file_path.suffix.lower().lstrip("."),
        size=stat.st_size,
        duration=duration,
        tags=tags,
        has_lyrics=is_valid_lyrics(tags.lyrics),
    )
    _track_cache[relative_path] = (stat.st_mtime, track)

    return track


def invalidate_track(path: str) -> None:
    """Drop a file from the caches so its next read comes from disk."""

    global _scan_cache

    _track_cache.pop(path, None)
    _scan_cache = None


def _collect_empty_directories(
    library_directory: Path, holds_audio: dict[str, bool]
) -> list[str]:
    """Reduce a directory-to-audio map to the folders worth deleting.

    A folder is empty when no audio file sits anywhere beneath it. Only the
    outermost one is reported: an artist folder holding nothing but empty album
    folders is a single dead folder, not one per album.
    """

    root = str(library_directory)

    return sorted(
        str(Path(directory).relative_to(library_directory))
        for directory, audio in holds_audio.items()
        if not audio
        and directory != root
        and (
            os.path.dirname(directory) == root
            or holds_audio.get(os.path.dirname(directory), True)
        )
    )


def _walk_library() -> tuple[list[LibraryTrack], list[str]]:
    """Walk the library directory, reading every supported file and noting dead folders.

    The walk runs bottom-up so a folder's audio flag can fold in the flags of the
    subfolders below it, which have already been visited.
    """

    library_directory = get_library_directory()

    if not library_directory.is_dir():
        logger.warning(f"Library directory does not exist: {library_directory}")
        return [], []

    started_at = time.monotonic()
    tracks: list[LibraryTrack] = []
    seen: set[str] = set()
    holds_audio: dict[str, bool] = {}

    for root, directories, filenames in os.walk(library_directory, topdown=False):
        audio_filenames = [
            filename
            for filename in filenames
            if filename.lower().endswith(SUPPORTED_EXTENSIONS)
        ]

        for filename in audio_filenames:
            track = read_library_track(file_path=Path(root) / filename)

            if track:
                tracks.append(track)
                seen.add(track.path)

        holds_audio[root] = bool(audio_filenames) or any(
            holds_audio.get(os.path.join(root, directory), False)
            for directory in directories
        )

    for stale in set(_track_cache) - seen:
        _track_cache.pop(stale, None)

    empty_directories = _collect_empty_directories(library_directory, holds_audio)

    logger.info(
        f"Scanned {len(tracks)} files and {len(empty_directories)} empty folders "
        f"in {library_directory} in {time.monotonic() - started_at:.2f}s"
    )
    return sorted(tracks, key=lambda track: track.path.casefold()), empty_directories


def _cached_scan() -> tuple[list[LibraryTrack], list[str]]:
    """Return the cached walk of the library, rewalking it when the cache is cold.

    This blocks on disk I/O for as long as the walk takes, so it must never be
    called from the event loop. Route handlers that need it are declared `def`
    so FastAPI runs them in a worker thread.

    Results are cached for SCAN_CACHE_TTL and the walk is serialised, so a
    burst of requests costs one walk rather than one each. Within a walk, files
    whose modification time is unchanged are served from the per-file cache.
    """

    global _scan_cache

    with _scan_lock:
        cached = _scan_cache

        if cached and (time.monotonic() - cached[0]) < SCAN_CACHE_TTL:
            return cached[1], cached[2]

        tracks, empty_directories = _walk_library()
        _scan_cache = (time.monotonic(), tracks, empty_directories)

        return tracks, empty_directories


def scan_library() -> list[LibraryTrack]:
    """Read every supported audio file in the library, ordered by path."""

    return _cached_scan()[0]


def scan_empty_directories() -> list[str]:
    """List the library folders that hold no audio file, outermost first."""

    return _cached_scan()[1]


def filter_tracks(
    tracks: list[LibraryTrack],
    *,
    query: str = "",
    file_format: str = "",
    missing: str = "",
) -> list[LibraryTrack]:
    """Filter scanned tracks by free text, container format, and missing tags."""

    results = tracks

    if query:
        needle = normalize(query)
        results = [
            track
            for track in results
            if needle in normalize(track.filename)
            or needle in normalize(track.tags.title)
            or needle in normalize(track.tags.artist)
            or needle in normalize(track.tags.album)
            or needle in normalize(track.directory)
        ]

    if file_format:
        results = [track for track in results if track.format == file_format.lower()]

    if missing == "lyrics":
        results = [track for track in results if not track.has_lyrics]
    elif missing == "musicbrainz_id":
        results = [track for track in results if not track.tags.musicbrainz_id]
    elif missing == "any":
        results = [track for track in results if len(track.filled_fields()) < 7]

    return results


def _duplicate_key(track: LibraryTrack) -> str:
    """Build the identity a track shares with its copies in other formats.

    Tagged files are keyed on artist and title, so the same recording is caught
    wherever it sits on disk. Untagged files fall back to their folder and file
    name, which keeps two albums that both open with an `01` file apart.
    """

    title = normalize(track.tags.title)

    if not title:
        return f"{normalize(track.directory)}\0{normalize(Path(track.filename).stem)}"

    return f"{normalize(track.tags.artist)}\0{title}"


def count_duplicate_tracks(tracks: list[LibraryTrack]) -> int:
    """Count the tracks the library holds more than one file for.

    A track downloaded as both Opus and FLAC counts once, not twice: the number
    answers "how many tracks are duplicated", not "how many files are spare".
    """

    counts: dict[str, int] = {}

    for track in tracks:
        key = _duplicate_key(track)
        counts[key] = counts.get(key, 0) + 1

    return sum(1 for count in counts.values() if count > 1)


def summarize_library(
    tracks: list[LibraryTrack], empty_directories: int = 0
) -> dict[str, int]:
    """Count the library-wide gaps worth acting on."""

    return {
        "total": len(tracks),
        "missing_lyrics": sum(1 for track in tracks if not track.has_lyrics),
        "missing_musicbrainz_id": sum(
            1 for track in tracks if not track.tags.musicbrainz_id
        ),
        "lossless": sum(1 for track in tracks if track.format == "flac"),
        "duplicates": count_duplicate_tracks(tracks),
        "empty_directories": empty_directories,
    }
