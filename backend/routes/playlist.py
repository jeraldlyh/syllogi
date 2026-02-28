from fastapi import APIRouter
from pydantic import BaseModel

from db.models.playlist import Playlist, PlaylistProvider
from db.session import SessionDep
from db.playlist import _get_playlists, _create_playlist

router = APIRouter()


class CreatePlaylist(BaseModel):
    provider: PlaylistProvider
    playlistId: str
    playlistName: str
    username: str
    enabled: bool
    cronExpression: str


@router.get(
    path="",
    summary="Get playlists",
    description="Retrieve a list of all playlists.",
)
def get_playlists(session: SessionDep):
    playlists = _get_playlists(session=session)

    return [playlist.to_dict() for playlist in playlists]


@router.post(
    path="",
    summary="Create playlist",
    description="Create a new playlist.",
)
def create_playlist(item: CreatePlaylist, session: SessionDep):
    playlist = Playlist(
        provider=item.provider,
        playlist_id=item.playlistId,
        playlist_name=item.playlistName,
        username=item.username,
        enabled=item.enabled,
        cron_expression=item.cronExpression,
    )
    _create_playlist(session=session, playlist=playlist)

    return {"id": str(playlist.id)}
