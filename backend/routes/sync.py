import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel

from db.models.sync import Sync, SyncProvider
from db.models.sync import SyncSession, SyncStatus
from db.sync import (
    create_sync,
    delete_sync,
    get_sync_by_id,
    get_syncs,
    update_sync,
)
from db.session import SessionDep
from db.sync_session import create_sync_session
from lib.cron import create_job, delete_job, update_job
from lib.models.common import ExternalSync, ExternalTrack
from lib.providers.jellyfin import JellyfinProvider
from lib.sync import sync_playlist, sync_playlist_task
from lib.spotify import (
    get_spotify_playlist,
    get_spotify_playlist_songs,
)
from lib.utils import get_now
from lib.youtube import (
    get_youtube_playlist,
    get_youtube_playlist_songs,
)

router = APIRouter()
logger = logging.getLogger(__name__)


class CreateOrUpdateSyncRequest(BaseModel):
    provider: SyncProvider
    playlist_id: str
    playlist_name: str
    username: str
    enable_sync: bool
    enable_download: bool
    is_public: bool
    cron_expression: str


@router.get(
    path="/config",
    summary="Get sync configs",
    description="Retrieve a list of all sync configurations.",
    responses={
        200: {
            "description": "Sync configs retrieved successfully",
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
                                "is_public": False,
                                "cron_expression": "0 * * * *",
                            }
                        ],
                    }
                }
            },
        }
    },
)
def _get_sync_configs(session: SessionDep):
    configs = get_syncs(session=session)
    return [config.to_dict() for config in configs]


@router.post(
    path="/config",
    summary="Create sync config",
    description="Create a new sync configuration.",
    responses={
        200: {
            "description": "Sync config created successfully",
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
def _create_sync_config(item: CreateOrUpdateSyncRequest, session: SessionDep):
    sync = Sync(
        provider=item.provider,
        playlist_id=item.playlist_id,
        playlist_name=item.playlist_name,
        username=item.username,
        enable_sync=item.enable_sync,
        enable_download=item.enable_download,
        is_public=item.is_public,
        cron_expression=item.cron_expression,
    )
    create_sync(session=session, sync=sync)

    if sync.enable_sync:
        create_job(
            func=sync_playlist,
            kwargs={"sync_config": sync, "provider": JellyfinProvider()},
            cron_expression=sync.cron_expression,
            job_id=str(sync.id),
        )

    return {"id": str(sync.id)}


@router.put(
    path="/config/{id}",
    summary="Update sync config",
    description="Update an existing sync configuration by its ID.",
    responses={
        200: {
            "description": "Sync config updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {"message": "Sync config updated successfully"},
                    }
                }
            },
        },
        400: {
            "description": "Sync config not found",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 400,
                            "name": "Bad Request",
                            "message": "Unable to find sync config: <sync_id>",
                        },
                    }
                }
            },
        },
    },
)
async def _update_sync_config(
    id: str, item: CreateOrUpdateSyncRequest, session: SessionDep
):
    sync = get_sync_by_id(session=session, sync_id=id)

    if not sync:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to find sync config: {id}",
        )

    sync.provider = item.provider
    sync.playlist_id = item.playlist_id
    sync.playlist_name = item.playlist_name
    sync.username = item.username
    sync.enable_sync = item.enable_sync
    sync.enable_download = item.enable_download
    sync.is_public = item.is_public
    sync.cron_expression = item.cron_expression

    jellyfin = JellyfinProvider()
    update_sync(session=session, sync=sync)

    await jellyfin.update_playlist_visibility(
        playlist_name=sync.playlist_name,
        username=sync.username,
        is_public=sync.is_public,
    )

    if not sync.enable_sync:
        delete_job(job_id=id)
    else:
        update_job(
            func=sync_playlist,
            kwargs={"sync_config": sync, "provider": jellyfin},
            cron_expression=sync.cron_expression,
            job_id=str(sync.id),
        )

    return {"message": "Sync config updated successfully"}


@router.delete(
    path="/config/{sync_id}",
    summary="Delete sync config",
    description="Delete a sync configuration by its ID.",
    responses={
        200: {
            "description": "Sync config deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {"message": "Sync config deleted successfully"},
                    }
                }
            },
        },
        400: {
            "description": "Sync config not found",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 400,
                            "name": "Bad Request",
                            "message": "Unable to find sync config: <sync_id>",
                        },
                    }
                }
            },
        },
    },
)
def _delete_sync_config(sync_id: str, session: SessionDep):
    sync = get_sync_by_id(session=session, sync_id=sync_id)

    if not sync:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to find sync config: {sync_id}",
        )

    delete_sync(session=session, sync=sync)
    delete_job(job_id=sync_id)

    return {"message": "Sync config deleted successfully"}


@router.post(
    path="",
    summary="Sync playlist",
    description="Sync a playlist (Spotify/Youtube) to Jellyfin.",
    responses={
        200: {
            "description": "Sync session created",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {"id": "2baf7b6b-87de-4289-bdd8-42f138f8c9e1"},
                    }
                }
            },
        },
        404: {
            "description": "Playlist not found",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 404,
                            "name": "Not Found",
                            "message": "Unable to find playlist: <playlist_id>",
                        },
                    }
                }
            },
        },
    },
)
def sync_playlist_endpoint(
    item: Sync, background_tasks: BackgroundTasks, session: SessionDep
) -> dict[str, str]:
    songs: list[ExternalTrack] = []
    external_playlist: ExternalSync | None = None

    match item.provider:
        case SyncProvider.spotify:
            songs = get_spotify_playlist_songs(playlist_id=item.playlist_id)
            external_playlist = get_spotify_playlist(playlist_id=item.playlist_id)
        case SyncProvider.youtube:
            songs = get_youtube_playlist_songs(playlist_id=item.playlist_id)
            external_playlist = get_youtube_playlist(playlist_id=item.playlist_id)

    internal_sync = get_sync_by_id(session=session, sync_id=item.id)

    if not internal_sync or not external_playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unable to find playlist: {item.playlist_id}",
        )

    playlist_id = internal_sync.playlist_id
    username = item.username
    started_at = get_now()
    jellyfin = JellyfinProvider()

    sync_session = SyncSession(
        provider=internal_sync.provider,
        provider_playlist_id=playlist_id,
        provider_playlist_name="",
        target_user_id="",
        target_username=username,
        target_playlist_id="",
        target_playlist_name="",
        started_at=started_at,
        finished_at=started_at,
        duration_seconds=0,
        status=SyncStatus.pending,
    )
    create_sync_session(session=session, sync_session=sync_session)

    background_tasks.add_task(
        sync_playlist_task,
        provider=jellyfin,
        internal_playlist_id=internal_sync.id,
        external_playlist=external_playlist,
        songs=songs,
        sync_session_id=sync_session.id,
    )

    return {"id": str(sync_session.id)}
