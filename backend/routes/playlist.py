from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.models.playlist import Playlist, PlaylistProvider
from db.session import SessionDep
from db.playlist import (
    _get_playlists,
    _get_playlist_by_id,
    _create_playlist,
    _update_playlist,
    _delete_playlist,
)

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


@router.put(
    path="/{playlist_id}",
    summary="Update playlist",
    description="Update an existing playlist by its ID.",
)
def update_playlist(playlist_id: str, item: CreatePlaylist, session: SessionDep):
    playlist = _get_playlist_by_id(session=session, playlist_id=playlist_id)

    if not playlist:
        raise HTTPException(
            status_code=400, detail=f"Unable to find playlist: {playlist_id}"
        )

    playlist.provider = item.provider
    playlist.playlist_id = item.playlistId
    playlist.playlist_name = item.playlistName
    playlist.username = item.username
    playlist.enabled = item.enabled
    playlist.cron_expression = item.cronExpression

    _update_playlist(session=session, playlist=playlist)

    return {"message": "Playlist updated successfully"}


@router.delete(
    path="/{playlist_id}",
    summary="Delete playlist",
    description="Delete a playlist by its ID.",
)
def delete_playlist(playlist_id: str, session: SessionDep):
    playlist = _get_playlist_by_id(session=session, playlist_id=playlist_id)

    if not playlist:
        raise HTTPException(
            status_code=400, detail=f"Unable to find playlist: {playlist_id}"
        )

    _delete_playlist(session=session, playlist=playlist)

    return {"message": "Playlist deleted successfully"}
