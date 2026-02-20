from typing import Sequence
import uuid

from sqlmodel import desc, select
from db.models.sync_session import SyncSession, SyncSessionTrack, TrackListKind
from db.session import SessionDep


def _create_sync_session(session: SessionDep, sync_session: SyncSession) -> None:
    session.add(sync_session)
    session.commit()
    session.refresh(sync_session)


def _update_sync_session(session: SessionDep, sync_session: SyncSession) -> None:
    session.add(sync_session)
    session.commit()
    session.refresh(sync_session)


def _get_sync_sessions(session: SessionDep) -> Sequence[SyncSession]:
    return session.exec(
        select(SyncSession).order_by(desc(SyncSession.created_at))
    ).all()


def _get_sync_session_tracks(
    session: SessionDep, sync_session_id: uuid.UUID
) -> Sequence[SyncSessionTrack]:
    return session.exec(
        select(SyncSessionTrack).where(
            SyncSessionTrack.sync_session_id == sync_session_id
        )
    ).all()


def _build_tracks(
    sync_session_id: uuid.UUID, names: list[str], kind: TrackListKind
) -> list[SyncSessionTrack]:
    return [
        SyncSessionTrack(sync_session_id=sync_session_id, kind=kind, name=name)
        for name in names
    ]
