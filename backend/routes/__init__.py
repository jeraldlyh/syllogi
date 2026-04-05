from fastapi import APIRouter, FastAPI

from routes.auth import router as auth_router
from routes.cron import router as cron_router
from routes.health import router as health_router
from routes.jellyfin import router as jellyfin_router
from routes.notification import router as notification_router
from routes.playlist import router as playlist_router
from routes.spotify import router as spotify_router
from routes.sync import router as sync_router
from routes.sync_session import router as sync_session_router
from routes.track import router as track_router
from routes.youtube import router as youtube_router

OPENAPI_TAGS = [
    {"name": "Auth", "description": "Authentication and current-user endpoints."},
    {"name": "Health", "description": "Service health and readiness checks."},
    {"name": "Track", "description": "Track search and matching endpoints."},
    {"name": "Jellyfin", "description": "Jellyfin integration endpoints."},
    {"name": "Notification", "description": "Notification retrieval endpoints."},
    {
        "name": "Sync Session",
        "description": "Playlist sync session history and results.",
    },
    {"name": "Spotify", "description": "Spotify playlist and track endpoints."},
    {"name": "Playlist", "description": "Managed playlists configuration endpoints."},
    {"name": "Cron", "description": "Scheduler and cron job endpoints."},
    {"name": "YouTube", "description": "YouTube playlist and download endpoints."},
    {"name": "Sync", "description": "Playlist sync execution endpoints."},
]


def register_routes(app: FastAPI) -> None:
    api = APIRouter(prefix="/api")
    api.include_router(router=auth_router, prefix="/auth", tags=["Auth"])
    api.include_router(router=health_router, tags=["Health"])
    api.include_router(router=track_router, prefix="/track", tags=["Track"])
    api.include_router(router=jellyfin_router, prefix="/jellyfin", tags=["Jellyfin"])
    api.include_router(
        router=notification_router,
        prefix="/notification",
        tags=["Notification"],
    )
    api.include_router(
        router=sync_session_router,
        prefix="/sync_session",
        tags=["Sync Session"],
    )
    api.include_router(router=spotify_router, prefix="/spotify", tags=["Spotify"])
    api.include_router(router=playlist_router, prefix="/playlist", tags=["Playlist"])
    api.include_router(router=cron_router, prefix="/cron", tags=["Cron"])
    api.include_router(router=youtube_router, prefix="/youtube", tags=["YouTube"])
    api.include_router(router=sync_router, prefix="/sync", tags=["Sync"])
    app.include_router(api)
