import json
import logging
import logging.config
from http import HTTPStatus

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

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
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        if not request.url.path.startswith("/api"):
            return response

        content_type = response.headers.get("content-type", "").lower()
        is_json = "application/json" in content_type
        is_streaming = hasattr(response, "body_iterator")

        if is_streaming and not is_json:
            return response

        body: bytes = b""
        if is_streaming:
            async for chunk in response.body_iterator:  # type: ignore[attr-defined]
                if isinstance(chunk, memoryview):
                    chunk = chunk.tobytes()
                elif isinstance(chunk, bytearray):
                    chunk = bytes(chunk)
                elif isinstance(chunk, str):
                    chunk = chunk.encode("utf-8", "ignore")
                body += chunk
        else:
            rb = getattr(response, "body", b"")
            if isinstance(rb, (bytes, bytearray)):
                body = bytes(rb)
            elif isinstance(rb, str):
                body = rb.encode("utf-8", "ignore")
        content_type = response.headers.get("content-type", "").lower()
        is_json = "application/json" in content_type

        try:
            data = (
                json.loads(body) if is_json else body.decode("utf-8", errors="ignore")
            )
        except Exception:
            data = None

        if isinstance(data, dict) and any(
            k in data for k in ("success", "error", "data")
        ):
            return response

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

    return app


app = create_app()
