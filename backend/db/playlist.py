import uuid
from sqlmodel import select
from db.models.playlist import Playlist
from db.session import SessionDep


def get_playlists(session: SessionDep):
    return session.exec(select(Playlist)).all()


def get_playlist_by_id(
    session: SessionDep, playlist_id: str | uuid.UUID
) -> Playlist | None:
    return session.get(Playlist, playlist_id)


def create_playlist(session: SessionDep, playlist: Playlist) -> None:
    session.add(playlist)
    session.commit()
    session.refresh(playlist)


def update_playlist(session: SessionDep, playlist: Playlist) -> None:
    session.add(playlist)
    session.commit()
    session.refresh(playlist)


def delete_playlist(session: SessionDep, playlist: Playlist) -> None:
    session.delete(playlist)
    session.commit()
