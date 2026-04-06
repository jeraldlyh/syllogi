import uuid
from sqlmodel import select
from db.models.user import User
from db.session import SessionDep


def _get_users(session: SessionDep):
    return session.exec(select(User)).all()


def _get_user_by_id(session: SessionDep, user_id: str | uuid.UUID) -> User | None:
    return session.get(User, user_id)


def _get_user_by_username(session: SessionDep, username: str) -> User | None:
    return session.exec(select(User).where(User.username == username)).first()


def _create_user(session: SessionDep, user: User) -> None:
    session.add(user)
    session.commit()
    session.refresh(user)


def _update_user(session: SessionDep, user: User) -> None:
    session.add(user)
    session.commit()
    session.refresh(user)


def _delete_user(session: SessionDep, user: User) -> None:
    session.delete(user)
    session.commit()
