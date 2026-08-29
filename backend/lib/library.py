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
_scan_cache: tuple[float, list[LibraryTrack]] | None = None
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


def _walk_library() -> list[LibraryTrack]:
    """Walk the library directory and read the tags of every supported file."""

    library_directory = get_library_directory()

    if not library_directory.is_dir():
        logger.warning(f"Library directory does not exist: {library_directory}")
        return []

    started_at = time.monotonic()
    tracks: list[LibraryTrack] = []
    seen: set[str] = set()

    for root, _, filenames in os.walk(library_directory):
        for filename in filenames:
            if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
                continue

            track = read_library_track(Path(root) / filename)

            if track:
                tracks.append(track)
                seen.add(track.path)

    for stale in set(_track_cache) - seen:
        _track_cache.pop(stale, None)

    logger.info(
        f"Scanned {len(tracks)} files in {library_directory} "
        f"in {time.monotonic() - started_at:.2f}s"
    )
    return sorted(tracks, key=lambda track: track.path.casefold())


def scan_library() -> list[LibraryTrack]:
    """Read every supported audio file in the library, ordered by path.

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
            return cached[1]

        tracks = _walk_library()
        _scan_cache = (time.monotonic(), tracks)

        return tracks


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


def summarize_library(tracks: list[LibraryTrack]) -> dict[str, int]:
    """Count the library-wide gaps worth acting on."""

    return {
        "total": len(tracks),
        "missing_lyrics": sum(1 for track in tracks if not track.has_lyrics),
        "missing_musicbrainz_id": sum(
            1 for track in tracks if not track.tags.musicbrainz_id
        ),
        "lossless": sum(1 for track in tracks if track.format == "flac"),
    }
