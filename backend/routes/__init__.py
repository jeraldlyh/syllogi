from fastapi import APIRouter, FastAPI
from routes.health import router as health_router
from routes.track import router as track_router
from routes.jellyfin import router as jellyfin_router
from routes.spotify import router as spotify_router
from routes.notification import router as notification_router
from routes.sync_session import router as sync_session_router
from routes.playlist import router as playlist_router
from routes.cron import router as cron_router
from routes.youtube import router as youtube_router
from routes.sync import router as sync_router


def register_routes(app: FastAPI) -> None:
    api = APIRouter(prefix="/api")
    api.include_router(router=health_router)
    api.include_router(router=track_router, prefix="/track")
    api.include_router(router=jellyfin_router, prefix="/jellyfin")
    api.include_router(router=notification_router, prefix="/notification")
    api.include_router(router=sync_session_router, prefix="/sync_session")
    api.include_router(router=spotify_router, prefix="/spotify")
    api.include_router(router=playlist_router, prefix="/playlist")
    api.include_router(router=cron_router, prefix="/cron")
    api.include_router(router=youtube_router, prefix="/youtube")
    api.include_router(router=sync_router, prefix="/sync")
    app.include_router(api)
