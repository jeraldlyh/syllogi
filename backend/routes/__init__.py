from fastapi import FastAPI
from routes.health import router as health_router
from routes.track import router as track_router
from routes.jellyfin import router as jellyfin_router
from routes.spotify import router as spotify_router
from routes.notification import router as notification_router
from routes.sync_session import router as sync_session_router
from routes.playlist import router as playlist_router


def register_routes(app: FastAPI) -> None:
    app.include_router(router=health_router)
    app.include_router(router=track_router, prefix="/track")
    app.include_router(router=jellyfin_router, prefix="/jellyfin")
    app.include_router(router=notification_router, prefix="/notification")
    app.include_router(router=sync_session_router, prefix="/sync")
    app.include_router(router=spotify_router, prefix="/sync/spotify")
    app.include_router(router=playlist_router, prefix="/playlist")
