import json
import logging
import logging.config
from http import HTTPStatus
from typing import Callable

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from db.models.playlist import PlaylistProvider
from db.playlist import _get_playlists
from db.session import get_session
from lib.cron import _create_job
from lib.spotify import _sync_spotify_playlist
from routes import register_routes

load_dotenv()


logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s [%(module)s]: %(message)s",
            },
            "access": {
                "format": "[%(asctime)s] %(levelname)s [%(module)s]: %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "access": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn.error": {
                "level": "DEBUG",
                "handlers": ["default"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "DEBUG",
                "handlers": ["default"],
                "propagate": False,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["default"],
        },
    }
)

logger = logging.getLogger(__name__)


class ApiResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        response: Response = await call_next(request)

        if (
            not request.url.path.startswith("/api")
            or request.method == "OPTIONS"
            or response.status_code > 300
        ):
            return response

        body: bytes = b""
        async for chunk in response.body_iterator:  # type: ignore[attr-defined]
            body += chunk

        data = json.loads(body.decode("utf-8"))
        content = {"success": 200 <= response.status_code < 300, "data": data}
        formatted_response = JSONResponse(
            content=content, status_code=response.status_code
        )

        for k, v in response.headers.items():
            if k.lower() not in ("content-length", "content-type"):
                formatted_response.headers[k] = v
        return formatted_response


def create_app() -> FastAPI:
    app = FastAPI(root_path="/api")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(ApiResponseMiddleware)
    register_routes(app)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, e: HTTPException):
        try:
            name = HTTPStatus(e.status_code).phrase
        except Exception:
            name = "HTTP Error"
        payload = {
            "success": False,
            "error": {
                "code": e.status_code,
                "name": name,
                "message": e.detail,
            },
        }
        return JSONResponse(status_code=e.status_code, content=payload)

    @app.exception_handler(Exception)
    async def exception_handler(_, e: Exception):
        logger.exception("Unhandled exception")
        payload = {
            "success": False,
            "error": {
                "code": 500,
                "name": "Internal Server Error",
                "message": "Something went wrong",
            },
        }
        return JSONResponse(status_code=500, content=payload)

    @app.on_event("startup")
    def startup_event():
        logger.info("Starting up application and initializing cron jobs")
        session = next(get_session())

        playlists = _get_playlists(session=session)

        for playlist in playlists:
            if playlist.cron_expression:
                logger.info(
                    f"Registering cron job for playlist {playlist.id} with cron expression: {playlist.cron_expression}"
                )
                cron_func = (
                    _sync_spotify_playlist
                    if playlist.provider == PlaylistProvider.spotify
                    else lambda: None
                )
                _create_job(
                    func=cron_func,
                    kwargs={"item": playlist, "session": session},
                    cron_expression=playlist.cron_expression,
                )

    return app


app = create_app()
