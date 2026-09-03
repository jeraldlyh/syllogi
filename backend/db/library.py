from collections.abc import Iterable, Sequence
from typing import cast

import sqlalchemy as sa
from sqlalchemy import CursorResult
from sqlmodel import Session, col, select

from db.models.library import LibraryFolder, LibraryTrack
from lib.utils import normalize_unicode

CHUNK_SIZE = 500
DUPLICATE_KEY_SEPARATOR = "\x1f"

PRESERVED_COLUMNS = frozenset({"id", "path", "created_at", "updated_at"})
TRACK_COLUMNS = tuple(
    column.key
    for column in sa.inspect(LibraryTrack).columns
    if column.key not in PRESERVED_COLUMNS
)


def _chunked(items: Sequence, size: int = CHUNK_SIZE) -> Iterable[Sequence]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def get_track_fingerprints(session: Session) -> dict[str, tuple[float, int]]:
    """Map every known track path to the (mtime, size) it was last read at.

    The sweep diffs this against the filesystem to decide which files actually
    need their tags read again. Size is part of the fingerprint because two
    writes within the same filesystem timestamp granularity would otherwise
    look unchanged.
    """

    rows = session.exec(
        select(LibraryTrack.path, LibraryTrack.mtime, LibraryTrack.size)
    ).all()

    return {path: (mtime, size) for path, mtime, size in rows}


def get_track_by_path(session: Session, path: str) -> LibraryTrack | None:
    return session.exec(
        select(LibraryTrack).where(col(LibraryTrack.path) == path)
    ).first()


def upsert_tracks(session: Session, tracks: Sequence[LibraryTrack]) -> None:
    """Insert or refresh the given tracks, matched on their library-relative path."""

    if not tracks:
        return

    existing = {
        track.path: track
        for chunk in _chunked([track.path for track in tracks])
        for track in session.exec(
            select(LibraryTrack).where(col(LibraryTrack.path).in_(chunk))
        ).all()
    }

    for track in tracks:
        current = existing.get(track.path)

        if current is None:
            session.add(track)
            continue

        for column in TRACK_COLUMNS:
            setattr(current, column, getattr(track, column))

        session.add(current)
    session.commit()


def delete_tracks_by_paths(session: Session, paths: Sequence[str]) -> int:
    """Drop the given paths from the library, returning how many rows were deleted."""

    if not paths:
        return 0

    deleted = 0

    for chunk in _chunked(paths):
        result = cast(
            CursorResult,
            session.execute(
                sa.delete(LibraryTrack).where(col(LibraryTrack.path).in_(chunk))
            ),
        )
        deleted += result.rowcount or 0

    session.commit()

    return deleted


def replace_empty_folders(session: Session, paths: Sequence[str]) -> None:
    """Swap the stored empty-folder list for the one the latest sweep found."""

    session.execute(sa.delete(LibraryFolder))

    for path in paths:
        session.add(LibraryFolder(path=path))

    session.commit()


def get_empty_folders(session: Session) -> Sequence[LibraryFolder]:
    return session.exec(select(LibraryFolder).order_by(LibraryFolder.path)).all()


def _search_condition(query: str):
    """Match a free-text needle against the fields to search."""

    needle = f"%{normalize_unicode(query).strip()}%"

    return sa.or_(
        col(LibraryTrack.filename).ilike(needle),
        col(LibraryTrack.title).ilike(needle),
        col(LibraryTrack.artist).ilike(needle),
        col(LibraryTrack.album).ilike(needle),
        col(LibraryTrack.directory).ilike(needle),
    )


def _filter_conditions(query: str, file_format: str, missing: str) -> list:
    conditions = []

    if query:
        conditions.append(_search_condition(query))

    if file_format:
        conditions.append(col(LibraryTrack.format) == file_format.lower())

    if missing == "lyrics":
        conditions.append(col(LibraryTrack.has_lyrics).is_(False))
    elif missing == "musicbrainz_id":
        conditions.append(col(LibraryTrack.musicbrainz_id) == "")
    elif missing == "any":
        conditions.append(
            sa.or_(
                col(LibraryTrack.title) == "",
                col(LibraryTrack.artist) == "",
                col(LibraryTrack.album) == "",
                col(LibraryTrack.date) == "",
                col(LibraryTrack.musicbrainz_id) == "",
                col(LibraryTrack.has_lyrics).is_(False),
                sa.func.json_array_length(col(LibraryTrack.genres)) == 0,
            )
        )

    return conditions


def query_tracks(
    session: Session,
    *,
    query: str = "",
    file_format: str = "",
    missing: str = "",
    limit: int = 100,
    offset: int = 0,
) -> tuple[Sequence[LibraryTrack], int]:
    """Return one page of matching tracks alongside the total match count."""

    conditions = _filter_conditions(
        query=query, file_format=file_format, missing=missing
    )

    matched = session.exec(
        select(sa.func.count()).select_from(LibraryTrack).where(*conditions)
    ).one()

    tracks = session.exec(
        select(LibraryTrack)
        .where(*conditions)
        .order_by(sa.func.lower(col(LibraryTrack.path)))
        .limit(limit)
        .offset(offset)
    ).all()

    return tracks, matched


def _duplicate_key_expression():
    """Build the identity a track shares with its copies in other formats."""

    stem = sa.func.substr(
        col(LibraryTrack.filename),
        1,
        sa.func.length(col(LibraryTrack.filename))
        - sa.func.length(col(LibraryTrack.format))
        - 1,
    )

    def lower(value):
        return sa.func.lower(value, type_=sa.Text)

    return sa.case(
        (
            col(LibraryTrack.title) == "",
            lower(col(LibraryTrack.directory)) + DUPLICATE_KEY_SEPARATOR + lower(stem),
        ),
        else_=lower(col(LibraryTrack.artist))
        + DUPLICATE_KEY_SEPARATOR
        + lower(col(LibraryTrack.title)),
    )


def duplicate_groups():
    """Select the duplicate keys the library holds more than one file for."""

    duplicate_key = _duplicate_key_expression().label("duplicate_key")

    return (
        select(duplicate_key)
        .group_by(duplicate_key)
        .having(sa.func.count() > 1)
        .subquery()
    )


def count_duplicate_tracks(session: Session) -> int:
    """Count the tracks the library holds more than one file for."""

    return session.exec(select(sa.func.count()).select_from(duplicate_groups())).one()


def summarize_library(session: Session) -> dict[str, int]:
    """Count the library-wide gaps worth acting on, in a single pass over the table."""

    def total_where(condition) -> sa.Case:
        return sa.case((condition, 1), else_=0)

    row = session.exec(
        select(
            sa.func.count(),
            sa.func.coalesce(
                sa.func.sum(total_where(col(LibraryTrack.has_lyrics).is_(False))), 0
            ),
            sa.func.coalesce(
                sa.func.sum(total_where(col(LibraryTrack.musicbrainz_id) == "")), 0
            ),
            sa.func.coalesce(
                sa.func.sum(total_where(col(LibraryTrack.format) == "flac")), 0
            ),
        ).select_from(LibraryTrack)
    ).one()

    total, missing_lyrics, missing_musicbrainz_id, lossless = row

    empty_directories = session.exec(
        select(sa.func.count()).select_from(LibraryFolder)
    ).one()

    return {
        "total": total,
        "missing_lyrics": missing_lyrics,
        "missing_musicbrainz_id": missing_musicbrainz_id,
        "lossless": lossless,
        "duplicates": count_duplicate_tracks(session),
        "empty_directories": empty_directories,
    }
