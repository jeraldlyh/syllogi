from collections.abc import Sequence

from sqlmodel import select

from db.models.notification import Notification
from db.session import SessionDep


def get_notifications(session: SessionDep) -> Sequence[Notification]:
    return session.exec(select(Notification)).all()
