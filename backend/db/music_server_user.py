from typing import Sequence
import uuid

from sqlmodel import select

from db.models.music_server_user import MusicServerProvider, MusicServerUser
from db.session import SessionDep


def get_music_server_users(session: SessionDep):
    return session.exec(select(MusicServerUser)).all()


def get_music_server_user_by_id(
    session: SessionDep, user_id: str | uuid.UUID
) -> MusicServerUser | None:
    return session.get(MusicServerUser, user_id)


def get_music_server_user_by_username(
    session: SessionDep, username: str, provider: MusicServerProvider
) -> MusicServerUser | None:
    return session.exec(
        select(MusicServerUser).where(
            MusicServerUser.username == username,
            MusicServerUser.provider == provider,
        )
    ).first()


def get_music_server_users_by_provider(
    session: SessionDep, provider: MusicServerProvider
) -> Sequence[MusicServerUser]:
    return session.exec(
        select(MusicServerUser).where(MusicServerUser.provider == provider)
    ).all()


def create_music_server_user(session: SessionDep, user: MusicServerUser) -> None:
    session.add(user)
    session.commit()
    session.refresh(user)


def update_music_server_user(session: SessionDep, user: MusicServerUser) -> None:
    session.add(user)
    session.commit()
    session.refresh(user)


def delete_music_server_user(session: SessionDep, user: MusicServerUser) -> None:
    session.delete(user)
    session.commit()
