from typing import Sequence
import uuid

from sqlmodel import desc, select
from db.models.sync_session import SyncSession, SyncSessionTrack, TrackListKind
from db.session import SessionDep


def create_sync_session(session: SessionDep, sync_session: SyncSession) -> None:
    session.add(sync_session)
    session.commit()
    session.refresh(sync_session)


def update_sync_session(session: SessionDep, sync_session: SyncSession) -> SyncSession:
    sync_session = session.merge(sync_session)
    session.commit()
    session.refresh(sync_session)
    return sync_session


def get_sync_sessions(session: SessionDep) -> Sequence[SyncSession]:
    return session.exec(
        select(SyncSession).order_by(desc(SyncSession.created_at))
    ).all()


def get_sync_session_tracks(
    session: SessionDep, sync_session_id: uuid.UUID
) -> Sequence[SyncSessionTrack]:
    return session.exec(
        select(SyncSessionTrack).where(
            SyncSessionTrack.sync_session_id == sync_session_id
        )
    ).all()


def build_tracks(
    sync_session_id: uuid.UUID, names: list[str], kind: TrackListKind
) -> list[SyncSessionTrack]:
    return [
        SyncSessionTrack(sync_session_id=sync_session_id, kind=kind, name=name)
        for name in names
    ]
