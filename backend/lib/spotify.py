import sys

from pathlib import Path
from typing import List
from flask import current_app


BASE_DIR = Path(__file__).resolve().parent.parent
SPOTAPI_DIR = BASE_DIR / "SpotAPI"

if SPOTAPI_DIR.exists():
    sys.path.insert(0, str(SPOTAPI_DIR))
else:
    raise RuntimeError(
        f"SpotAPI submodule not found at {SPOTAPI_DIR}. Did you run `git submodule update --init --recursive`?"
    )

from spotapi.playlist import PublicPlaylist
from spotapi.album import PublicAlbum


def get_songs_by_playlist(playlist_id: str) -> List[dict]:
    offset = 0
    limit = 50
    songs = []

    playlist = PublicPlaylist(playlist_id)
    playlist_info = playlist.get_playlist_info(limit=limit)

    while offset < playlist_info["data"]["playlistV2"]["content"]["totalCount"]:
        songs.extend(playlist_info["data"]["playlistV2"]["content"]["items"])
        offset += limit
        playlist_info = playlist.get_playlist_info(offset=offset, limit=limit)
        current_app.logger.info(f"Fetched {len(songs)} songs...")

    current_app.logger.info(f"Total songs fetched: {len(songs)}")

    return songs


def get_album_by_id(album_id: str) -> dict:
    album = PublicAlbum(album_id)
    album_info = album.get_album_info()

    return album_info
