from sqlmodel import select
from db.models.playlist import Playlist
from db.session import SessionDep


def _get_playlists(session: SessionDep):
    return session.exec(select(Playlist)).all()


def _get_playlist_by_id(session: SessionDep, playlist_id: str):
    return session.get(Playlist, playlist_id)


def _create_playlist(session: SessionDep, playlist: Playlist) -> None:
    session.add(playlist)
    session.commit()
    session.refresh(playlist)


def _update_playlist(session: SessionDep, playlist: Playlist) -> None:
    session.add(playlist)
    session.commit()
    session.refresh(playlist)


def _delete_playlist(session: SessionDep, playlist: Playlist) -> None:
    session.delete(playlist)
    session.commit()
