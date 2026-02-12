from typing import Sequence
from sqlmodel import select
from db.session import SessionDep
from db.models.notification import Notification


def _get_all_notifications(session: SessionDep) -> Sequence[Notification]:
    return session.exec(select(Notification)).all()
