from typing import Sequence
import uuid

from sqlmodel import desc, select
from db.models.import_session import ImportSession, ImportSessionTrack, TrackListKind
from db.session import SessionDep


def _create_import_session(session: SessionDep, import_session: ImportSession) -> None:
    session.add(import_session)
    session.commit()
    session.refresh(import_session)


def _get_import_sessions(session: SessionDep) -> Sequence[ImportSession]:
    return session.exec(
        select(ImportSession).order_by(desc(ImportSession.created_at))
    ).all()


def _get_import_session_tracks(
    session: SessionDep, import_session_id: uuid.UUID
) -> Sequence[ImportSessionTrack]:
    return session.exec(
        select(ImportSessionTrack).where(
            ImportSessionTrack.import_session_id == import_session_id
        )
    ).all()


def _build_tracks(
    import_session_id: uuid.UUID, names: list[str], kind: TrackListKind
) -> list[ImportSessionTrack]:
    return [
        ImportSessionTrack(import_session_id=import_session_id, kind=kind, name=name)
        for name in names
    ]
