from db.models.playlist import Playlist, PlaylistProvider
from db.session import SessionDep
from lib.spotify import _sync_spotify_playlist


def _sync_playlist(playlist: Playlist, session: SessionDep) -> dict[str, str]:
    match playlist.provider:
        case PlaylistProvider.spotify:
            return _sync_spotify_playlist(item=playlist, session=session)
        case _:
            return {}
