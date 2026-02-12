from fastapi import FastAPI
from routes.health import router as health_router
from routes.track import router as track_router
from routes.user import router as user_router
from routes.spotify import router as spotify_router
from routes.notification import router as notification_router
from routes.import_session import router as import_session_router


def register_routes(app: FastAPI) -> None:
    app.include_router(router=health_router)
    app.include_router(router=track_router, prefix="/track")
    app.include_router(router=user_router, prefix="/user")
    app.include_router(router=notification_router, prefix="/notification")
    app.include_router(router=import_session_router, prefix="/import")
    app.include_router(router=spotify_router, prefix="/import/spotify")
