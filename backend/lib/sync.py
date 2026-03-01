from db.models.playlist import Playlist
from lib.spotify import _sync_spotify_playlist


def sync_playlist(playlist: Playlist):
    match playlist.provider:
        case "spotify":
            return _sync_spotify_playlist(playlist=playlist)
        case _:
            return
