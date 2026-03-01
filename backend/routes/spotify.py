import logging
from typing import Annotated, Any, Mapping

from fastapi import APIRouter, Path
from pydantic import BaseModel

from db.models.playlist import Playlist
from db.session import SessionDep
from lib.spotify import _get_playlist
from lib.sync import _sync_playlist

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
def get_playlist(
    id: Annotated[str, Path(min_length=1, description="Spotify Playlist ID")],
) -> Mapping[str, Any]:
    return _get_playlist(id)


@router.post(
    path="",
    summary="Sync playlist",
    description="Sync a Spotify playlist to Jellyfin.",
)
def sync_playlist(item: Playlist, session: SessionDep) -> dict[str, str]:
    return _sync_playlist(
        playlist=item,
        session=session,
    )
