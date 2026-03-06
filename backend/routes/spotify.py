import logging
from typing import Annotated, Any, Mapping

from fastapi import APIRouter, Path
from pydantic import BaseModel

from lib.spotify import (
    _get_spotify_playlist,
    _get_spotify_playlist_songs,
)

router = APIRouter()
logger = logging.getLogger(__name__)


class ImportPlaylist(BaseModel):
    playlist_id: str
    username: str


@router.get(
    path="/{id}",
    summary="Get playlist",
    description="Retrieve a Spotify playlist by its ID.",
)
def get_spotify_playlist(
    id: Annotated[str, Path(min_length=1, description="Spotify Playlist ID")],
) -> Mapping[str, Any]:
    playlist = _get_spotify_playlist(id)

    return playlist.to_dict()


@router.get(
    path="/{id}/songs",
    summary="Get Spotify playlist songs",
    description="Retrieve a Spotify playlist songs by its ID.",
)
def get_spotify_playlist_songs(
    id: Annotated[str, Path(min_length=1, description="Spotify Playlist ID")],
) -> list[dict[str, Any]]:
    songs = _get_spotify_playlist_songs(playlist_id=id)

    return [song.to_dict() for song in songs]
