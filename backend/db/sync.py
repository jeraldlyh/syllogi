import uuid
from sqlmodel import select
from db.models.sync import Sync
from db.session import SessionDep


def get_syncs(session: SessionDep):
    return session.exec(select(Sync)).all()


def get_sync_by_id(
    session: SessionDep, sync_id: str | uuid.UUID
) -> Sync | None:
    return session.get(Sync, sync_id)


def create_sync(session: SessionDep, sync: Sync) -> None:
    session.add(sync)
    session.commit()
    session.refresh(sync)


def update_sync(session: SessionDep, sync: Sync) -> None:
    session.add(sync)
    session.commit()
    session.refresh(sync)


def delete_sync(session: SessionDep, sync: Sync) -> None:
    session.delete(sync)
    session.commit()
