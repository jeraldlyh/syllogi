import json
import logging
import logging.config
import os
from http import HTTPStatus
from typing import Callable

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from db.sync import get_syncs
from db.recommendation import get_recommendations
from db.models.music_server_user import MusicServerProvider, MusicServerUser
from db.music_server_user import (
    create_music_server_user,
    get_music_server_user_by_username,
)
from db.session import get_isolated_session
from lib.cron import create_job, scheduler
from lib.env import get_environment_variable
from lib.providers import get_provider
from lib.providers.navidrome import NavidromeProvider
from lib.recommendation import generate_recommendations
from lib.sync import sync_playlist
from routes import OPENAPI_TAGS, register_routes

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


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
                "level": LOG_LEVEL,
                "handlers": ["default"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": LOG_LEVEL,
                "handlers": ["default"],
                "propagate": False,
            },
        },
        "root": {
            "level": LOG_LEVEL,
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


async def ensure_navidrome_user(provider: NavidromeProvider) -> None:
    """Validate Navidrome admin credentials and seed the MusicServerUser in the database.

    Raises:
        RuntimeError: If the admin credentials are invalid.
    """
    username = str(get_environment_variable("NAVIDROME_USERNAME", ignore_error=False))
    password = str(get_environment_variable("NAVIDROME_PASSWORD", ignore_error=False))

    if not await provider.verify_user_credentials(username, password):
        raise RuntimeError(
            "Navidrome admin credentials are invalid. "
            "Check NAVIDROME_USERNAME and NAVIDROME_PASSWORD environment variables."
        )

    with get_isolated_session() as session:
        existing_user = get_music_server_user_by_username(
            session=session,
            username=username,
            provider=MusicServerProvider.navidrome,
        )

        if not existing_user:
            new_user = MusicServerUser(
                username=username,
                provider=MusicServerProvider.navidrome,
                password=password,
            )
            create_music_server_user(session=session, user=new_user)
    logger.info("Navidrome credentials verified, admin user seeded in database")


def create_cron_jobs():
    logger.info("Starting up application and initializing cron jobs")

    provider = get_provider()

    with get_isolated_session() as session:
        syncs = get_syncs(session=session)
        recommendations = get_recommendations(session=session)

    for sync_config in syncs:
        if sync_config.cron_expression:
            logger.info(
                f"Registering cron job for sync config {sync_config.id} with cron expression: {sync_config.cron_expression}"
            )
            create_job(
                func=sync_playlist,
                kwargs={"sync_config": sync_config, "provider": provider},
                cron_expression=sync_config.cron_expression,
                job_id=str(sync_config.id),
            )

    for recommendation in recommendations:
        if recommendation.cron_expression:
            logger.info(
                f"Registering cron job for recommendation {recommendation.id} with cron expression: {recommendation.cron_expression}"
            )
            create_job(
                func=generate_recommendations,
                kwargs={"recommendation": recommendation, "provider": provider},
                cron_expression=recommendation.cron_expression,
                job_id=str(recommendation.id),
            )


def create_app() -> FastAPI:
    app = FastAPI(
        openapi_tags=OPENAPI_TAGS,
        responses={
            401: {
                "description": "Invalid authentication credentials",
                "content": {
                    "application/json": {
                        "example": {
                            "success": False,
                            "error": {
                                "code": 401,
                                "name": "Unauthorized",
                                "message": "Invalid authentication credentials",
                            },
                        }
                    }
                },
            },
        },
    )
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
    async def startup_event():
        scheduler.start()

        provider = get_provider()
        await provider.ensure_download_library_exists()

        if isinstance(provider, NavidromeProvider):
            await ensure_navidrome_user(provider)

        create_cron_jobs()

    @app.on_event("shutdown")
    def shutdown_event():
        scheduler.shutdown()

    return app


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Bearer token in Authorization header, or access_token cookie",
        }
    }

    openapi_schema["security"] = [{"Bearer Auth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app = create_app()
app.openapi = custom_openapi
