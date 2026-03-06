import logging
from typing import Annotated, Any

from fastapi import APIRouter, Path

from lib.youtube import (
    _get_youtube_playlist,
    _get_youtube_playlist_songs,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    path="/{id}",
    summary="Get YouTube playlist",
    description="Retrieve a YouTube playlist by its ID.",
)
def get_youtube_playlist(
    id: Annotated[str, Path(min_length=1, description="YouTube Playlist ID")],
) -> dict[str, Any]:
    playlist = _get_youtube_playlist(id)

    return playlist.to_dict()


@router.get(
    path="/{id}/songs",
    summary="Get YouTube playlist songs",
    description="Retrieve a YouTube playlist songs by its ID.",
)
def get_youtube_playlist_songs(
    id: Annotated[str, Path(min_length=1, description="YouTube Playlist ID")],
) -> list[dict[str, Any]]:
    songs = _get_youtube_playlist_songs(playlist_id=id)

    return [song.to_dict() for song in songs]
