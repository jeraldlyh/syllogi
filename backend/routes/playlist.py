from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.models.playlist import Playlist, PlaylistProvider
from db.playlist import (
    _create_playlist,
    _delete_playlist,
    _get_playlist_by_id,
    _get_playlists,
    _update_playlist,
)
from db.session import SessionDep
from lib.sync import _sync_playlist
from lib.cron import _delete_job, _update_job, _create_job

router = APIRouter()


class CreateOrUpdatePlaylist(BaseModel):
    provider: PlaylistProvider
    playlist_id: str
    playlist_name: str
    username: str
    enabled: bool
    cron_expression: str


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
def create_playlist(item: CreateOrUpdatePlaylist, session: SessionDep):
    playlist = Playlist(
        provider=item.provider,
        playlist_id=item.playlist_id,
        playlist_name=item.playlist_name,
        username=item.username,
        enabled=item.enabled,
        cron_expression=item.cron_expression,
    )
    _create_playlist(session=session, playlist=playlist)

    if playlist.enabled:
        _create_job(
            func=_sync_playlist,
            kwargs={"playlist": playlist, "session": session},
            cron_expression=playlist.cron_expression,
        )

    return {"id": str(playlist.id)}


@router.put(
    path="/{playlist_id}",
    summary="Update playlist",
    description="Update an existing playlist by its ID.",
)
def update_playlist(
    playlist_id: str, item: CreateOrUpdatePlaylist, session: SessionDep
):
    playlist = _get_playlist_by_id(session=session, playlist_id=playlist_id)

    if not playlist:
        raise HTTPException(
            status_code=400, detail=f"Unable to find playlist: {playlist_id}"
        )

    playlist.provider = item.provider
    playlist.playlist_id = item.playlist_id
    playlist.playlist_name = item.playlist_name
    playlist.username = item.username
    playlist.enabled = item.enabled
    playlist.cron_expression = item.cron_expression

    _update_playlist(session=session, playlist=playlist)

    if not playlist.enabled:
        _delete_job(playlist_id=playlist_id)
    else:
        _update_job(
            func=_sync_playlist,
            kwargs={"playlist": playlist, "session": session},
            cron_expression=playlist.cron_expression,
        )

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
    _delete_job(playlist_id=playlist_id)

    return {"message": "Playlist deleted successfully"}
