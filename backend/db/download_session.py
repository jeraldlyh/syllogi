from typing import Sequence
import uuid

from sqlmodel import desc, select
from db.models.download_session import DownloadSession
from db.session import SessionDep


def create_download_session(
    session: SessionDep, download_session: DownloadSession
) -> DownloadSession:
    session.add(download_session)
    session.commit()
    session.refresh(download_session)
    return download_session


def update_download_session(
    session: SessionDep, download_session: DownloadSession
) -> DownloadSession:
    download_session = session.merge(download_session)
    session.commit()
    session.refresh(download_session)
    return download_session


def get_download_session_by_id(
    session: SessionDep, download_session_id: uuid.UUID
) -> DownloadSession | None:
    return session.get(DownloadSession, download_session_id)


def get_download_sessions(
    session: SessionDep, limit: int = 20
) -> Sequence[DownloadSession]:
    return session.exec(
        select(DownloadSession).order_by(desc(DownloadSession.created_at)).limit(limit)
    ).all()
