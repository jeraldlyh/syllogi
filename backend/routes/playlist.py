from fastapi import APIRouter, HTTPException, status
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


class CreateOrUpdatePlaylistRequest(BaseModel):
    provider: PlaylistProvider
    playlist_id: str
    playlist_name: str
    username: str
    enable_sync: bool
    enable_download: bool
    cron_expression: str


@router.get(
    path="",
    summary="Get playlists",
    description="Retrieve a list of all playlists.",
    responses={
        200: {
            "description": "Playlists retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "id": "2baf7b6b-87de-4289-bdd8-42f138f8c9e1",
                                "provider": "spotify",
                                "playlist_id": "37i9dQZF1DXcBWIGoYBM5M",
                                "playlist_name": "Today's Top Hits",
                                "username": "jerald",
                                "enable_sync": True,
                                "enable_download": False,
                                "cron_expression": "0 * * * *",
                            }
                        ],
                    }
                }
            },
        }
    },
)
def get_playlists(session: SessionDep):
    playlists = _get_playlists(session=session)

    return [playlist.to_dict() for playlist in playlists]


@router.post(
    path="",
    summary="Create playlist",
    description="Create a new playlist.",
    responses={
        200: {
            "description": "Playlist created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {"id": "2baf7b6b-87de-4289-bdd8-42f138f8c9e1"},
                    }
                }
            },
        }
    },
)
def create_playlist(item: CreateOrUpdatePlaylistRequest, session: SessionDep):
    playlist = Playlist(
        provider=item.provider,
        playlist_id=item.playlist_id,
        playlist_name=item.playlist_name,
        username=item.username,
        enable_sync=item.enable_sync,
        enable_download=item.enable_download,
        cron_expression=item.cron_expression,
    )
    _create_playlist(session=session, playlist=playlist)

    if playlist.enable_sync:
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
    responses={
        200: {
            "description": "Playlist updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {"message": "Playlist updated successfully"},
                    }
                }
            },
        },
        400: {
            "description": "Playlist not found",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 400,
                            "name": "Bad Request",
                            "message": "Unable to find playlist: <playlist_id>",
                        },
                    }
                }
            },
        },
    },
)
def update_playlist(
    playlist_id: str, item: CreateOrUpdatePlaylistRequest, session: SessionDep
):
    playlist = _get_playlist_by_id(session=session, playlist_id=playlist_id)

    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to find playlist: {playlist_id}",
        )

    playlist.provider = item.provider
    playlist.playlist_id = item.playlist_id
    playlist.playlist_name = item.playlist_name
    playlist.username = item.username
    playlist.enable_sync = item.enable_sync
    playlist.enable_download = item.enable_download
    playlist.cron_expression = item.cron_expression

    _update_playlist(session=session, playlist=playlist)

    if not playlist.enable_sync:
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
    responses={
        200: {
            "description": "Playlist deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {"message": "Playlist deleted successfully"},
                    }
                }
            },
        },
        400: {
            "description": "Playlist not found",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 400,
                            "name": "Bad Request",
                            "message": "Unable to find playlist: <playlist_id>",
                        },
                    }
                }
            },
        },
    },
)
def delete_playlist(playlist_id: str, session: SessionDep):
    playlist = _get_playlist_by_id(session=session, playlist_id=playlist_id)

    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to find playlist: {playlist_id}",
        )

    _delete_playlist(session=session, playlist=playlist)
    _delete_job(playlist_id=playlist_id)

    return {"message": "Playlist deleted successfully"}
