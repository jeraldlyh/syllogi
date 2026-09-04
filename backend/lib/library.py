import logging
import os
import shutil
import threading
import time
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, status
from sqlmodel import Session

from db.library import (
    delete_tracks_by_paths,
    get_empty_folders,
    get_track_fingerprints,
    replace_empty_folders,
    upsert_tracks,
)
from db.models.library import LibraryTrack
from db.session import get_isolated_session
from lib.env import get_environment_variable
from lib.tagger import (
    SUPPORTED_EXTENSIONS,
    is_synced_lyrics,
    is_valid_lyrics,
    read_audio_tags,
    resolve_existing_path,
)
from lib.utils import get_now, normalize_unicode, truncate

logger = logging.getLogger(__name__)

SWEEP_INTERVAL = 900
UPSERT_BATCH_SIZE = 100

_sweep_lock = threading.Lock()
_sweeping = False
_last_swept_at: float | None = None
_last_swept_on: datetime | None = None
_last_error: str | None = None


def get_library_directory() -> Path:
    """Return the resolved root directory holding the downloaded audio files."""

    return Path(str(get_environment_variable("DOWNLOAD_DIR"))).resolve()


def resolve_library_path(path: str) -> Path:
    """Resolve a library-relative path to an audio file on disk.

    Raises:
        HTTPException: If the path escapes the library, is not an audio file, or is missing.
    """

    library_directory = get_library_directory()
    resolved = Path(resolve_existing_path(os.path.realpath(library_directory / path)))

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


def read_library_track(file_path: Path) -> tuple[LibraryTrack, str] | None:
    """Read an audio file into an unsaved LibraryTrack and its lyrics body.

    Returns None if the tags cannot be read. The lyrics come back alongside the
    row rather than on it: the editor needs the text, but storing it on every row
    would bloat the table for a field no list query ever reads.

    `file_path` must be the path as it exists on disk. Everything stored on the row
    is normalised to NFC, so the database holds one spelling of a name regardless
    of how the filesystem chose to hand it over.
    """

    library_directory = get_library_directory()

    try:
        stat = file_path.stat()
    except OSError:
        return None

    result = read_audio_tags(str(file_path))

    if result is None:
        return None

    tags, duration = result
    directory = str(file_path.parent.relative_to(library_directory))

    track = LibraryTrack(
        path=truncate(
            normalize_unicode(str(file_path.relative_to(library_directory))), 1024
        ),
        filename=truncate(normalize_unicode(file_path.name), 512),
        directory=(
            "" if directory == "." else truncate(normalize_unicode(directory), 1024)
        ),
        format=file_path.suffix.lower().lstrip("."),
        size=stat.st_size,
        duration=duration,
        mtime=stat.st_mtime,
        title=truncate(normalize_unicode(tags.title), 512),
        artist=truncate(normalize_unicode(tags.artist), 512),
        album=truncate(normalize_unicode(tags.album), 512),
        date=truncate(tags.date, 32),
        genres=[normalize_unicode(genre) for genre in tags.genres],
        musicbrainz_id=truncate(tags.musicbrainz_id, 64),
        has_lyrics=is_valid_lyrics(tags.lyrics),
        is_synced_lyrics=is_synced_lyrics(tags.lyrics),
    )

    return track, tags.lyrics


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
        normalize_unicode(str(Path(directory).relative_to(library_directory)))
        for directory, audio in holds_audio.items()
        if not audio
        and directory != root
        and (
            os.path.dirname(directory) == root
            or holds_audio.get(os.path.dirname(directory), True)
        )
    )


def _contains_audio(directory: Path) -> bool:
    """Check whether any audio file sits anywhere beneath a folder."""

    for _, _, filenames in os.walk(directory):
        if any(
            filename.lower().endswith(SUPPORTED_EXTENSIONS) for filename in filenames
        ):
            return True
    return False


def resolve_library_folder(path: str) -> Path | None:
    """Resolve a library-relative folder path to the folder it names on disk.

    Returns None if the path escapes the library, names the library root itself,
    or no longer points at a folder.
    """

    library_directory = get_library_directory()
    resolved = Path(resolve_existing_path(os.path.realpath(library_directory / path)))

    if library_directory not in resolved.parents:
        return None
    return resolved if resolved.is_dir() else None


def delete_empty_folders(session: Session) -> dict:
    """Delete every folder the last sweep found holding no audio.

    Returns the paths deleted and the paths kept.
    """

    deleted: list[str] = []
    kept: list[str] = []

    for folder in get_empty_folders(session):
        target = resolve_library_folder(folder.path)

        if target is None:
            logger.info(f"Empty folder is already gone: {folder.path}")
            continue

        if _contains_audio(target):
            logger.info(f"Keeping folder that contains audio: {folder.path}")
            kept.append(folder.path)
            continue

        try:
            shutil.rmtree(target)
            deleted.append(folder.path)
        except OSError as e:
            logger.warning(f"Could not delete empty folder {folder.path}: {e}")
            kept.append(folder.path)

    replace_empty_folders(session, kept)

    logger.info(f"Deleted {len(deleted)} empty folders, kept {len(kept)}")

    return {"deleted": deleted, "kept": kept}


def delete_library_tracks(session: Session, paths: Sequence[str]) -> dict:
    """Delete the named audio files from disk and drop their rows.

    Returns the paths deleted and the paths kept.
    """

    deleted: list[str] = []
    kept: list[str] = []

    for path in paths:
        try:
            target = resolve_library_path(path)
        except HTTPException as e:
            if e.status_code == status.HTTP_404_NOT_FOUND:
                logger.info(f"Library file is already gone: {path}")
                deleted.append(path)
            else:
                logger.warning(f"Refusing to delete {path}: {e.detail}")
                kept.append(path)
            continue

        try:
            target.unlink()
            deleted.append(path)
        except OSError as e:
            logger.warning(f"Could not delete library file {path}: {e}")
            kept.append(path)

    delete_tracks_by_paths(session, deleted)

    logger.info(f"Deleted {len(deleted)} library files, kept {len(kept)}")

    return {"deleted": deleted, "kept": kept}


def walk_library() -> tuple[dict[str, tuple[float, int, str]], list[str]]:
    """Stat every audio file in the library and note the folders holding none.

    Returns a map of library-relative path to (mtime, size, on-disk path),
    plus the empty folders.
    """

    library_directory = get_library_directory()

    if not library_directory.is_dir():
        logger.warning(f"Library directory does not exist: {library_directory}")
        return {}, []

    started_at = time.monotonic()
    files: dict[str, tuple[float, int, str]] = {}
    holds_audio: dict[str, bool] = {}

    for root, directories, filenames in os.walk(library_directory, topdown=False):
        audio_filenames = [
            filename
            for filename in filenames
            if filename.lower().endswith(SUPPORTED_EXTENSIONS)
        ]

        for filename in audio_filenames:
            file_path = Path(root) / filename

            try:
                stat = file_path.stat()
            except OSError:
                logger.warning(f"Could not stat library file: {file_path}")
                continue

            relative_path = normalize_unicode(
                str(file_path.relative_to(library_directory))
            )
            files[relative_path] = (stat.st_mtime, stat.st_size, str(file_path))

        holds_audio[root] = bool(audio_filenames) or any(
            holds_audio.get(os.path.join(root, directory), False)
            for directory in directories
        )

    empty_directories = _collect_empty_directories(library_directory, holds_audio)

    logger.info(
        f"Walked {len(files)} files and {len(empty_directories)} empty folders "
        f"in {library_directory} in {time.monotonic() - started_at:.2f}s"
    )
    return files, empty_directories


def sweep_library(session: Session) -> dict[str, int]:
    """Reconcile the database against the filesystem, reading only what changed.

    Files whose modification time and size still match their row are left alone,
    so a repeat sweep costs one stat per file rather than one tag read per file.
    """

    library_directory = get_library_directory()
    started_at = time.monotonic()

    files, empty_directories = walk_library()
    known = get_track_fingerprints(session=session)

    removed = delete_tracks_by_paths(
        session=session, paths=sorted(set(known) - set(files))
    )

    changed = [
        (path, on_disk_path)
        for path, (mtime, size, on_disk_path) in files.items()
        if known.get(path) != (mtime, size)
    ]

    read = 0
    unreadable = 0
    batch: list[LibraryTrack] = []

    for path, on_disk_path in changed:
        result = read_library_track(Path(on_disk_path))

        if result is None:
            logger.warning(f"Skipping unreadable library file: {path}")
            unreadable += 1
            continue

        batch.append(result[0])
        read += 1

        if len(batch) >= UPSERT_BATCH_SIZE:
            upsert_tracks(session, batch)
            batch = []

    upsert_tracks(session, batch)
    replace_empty_folders(session, empty_directories)

    logger.info(
        f"Swept {library_directory}: {len(files)} files, {read} read, "
        f"{removed} removed, {unreadable} unreadable, "
        f"{len(empty_directories)} empty folders in {time.monotonic() - started_at:.2f}s"
    )

    return {
        "total": len(files),
        "read": read,
        "removed": removed,
        "unreadable": unreadable,
        "empty_directories": len(empty_directories),
    }


def get_scan_state() -> dict:
    """Report whether a sweep is running and when one last finished."""

    with _sweep_lock:
        return {
            "scanning": _sweeping,
            "last_scanned_at": _last_swept_on.isoformat() if _last_swept_on else None,
            "error": _last_error,
        }


def _run_sweep() -> None:
    """Run one sweep on its own session, then release the running flag."""

    global _sweeping, _last_swept_at, _last_swept_on, _last_error

    try:
        with get_isolated_session() as session:
            sweep_library(session)

        error = None
    except Exception as e:
        logger.exception("Library sweep failed")
        error = str(e)

    with _sweep_lock:
        _sweeping = False
        _last_swept_at = time.monotonic()
        _last_swept_on = get_now()
        _last_error = error


def trigger_library_sweep(force: bool = False) -> bool:
    """Start a sweep in the background unless one is running or the last is still fresh.

    Returns whether a sweep was started. The walk blocks on network I/O for as
    long as it takes, so it never runs inside a request.
    """

    global _sweeping

    with _sweep_lock:
        if _sweeping:
            return False

        if (
            not force
            and _last_swept_at is not None
            and (time.monotonic() - _last_swept_at) < SWEEP_INTERVAL
        ):
            return False

        _sweeping = True

    threading.Thread(target=_run_sweep, name="library-sweep", daemon=True).start()

    return True
