import uuid

from sqlalchemy import func
from sqlmodel import select

from db.models.user import User
from db.session import SessionDep


def get_users(session: SessionDep):
    return session.exec(select(User)).all()


def get_user_by_id(session: SessionDep, user_id: str | uuid.UUID) -> User | None:
    return session.get(User, user_id)


def get_user_by_username(session: SessionDep, username: str) -> User | None:
    return session.exec(select(User).where(User.username == username)).first()


def get_user_by_oauth_id(session: SessionDep, oauth_id: str) -> User | None:
    return session.exec(select(User).where(User.oauth_id == oauth_id)).first()


def count_users(session: SessionDep) -> int:
    return session.exec(select(func.count()).select_from(User)).one()


def create_user(session: SessionDep, user: User) -> None:
    session.add(user)
    session.commit()
    session.refresh(user)


def update_user(session: SessionDep, user: User) -> None:
    session.add(user)
    session.commit()
    session.refresh(user)


def delete_user(session: SessionDep, user: User) -> None:
    session.delete(user)
    session.commit()
