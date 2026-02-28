from sqlmodel import select
from db.models.playlist import Playlist
from db.session import SessionDep


def _get_playlists(session: SessionDep):
    return session.exec(select(Playlist)).all()


def _create_playlist(session: SessionDep, playlist: Playlist) -> None:
    session.add(playlist)
    session.commit()
    session.refresh(playlist)
