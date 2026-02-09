import json
import logging
from http import HTTPStatus

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from lib.db import create_db_and_tables
from routes import register_routes

load_dotenv()


logger = logging.getLogger(__name__)


class ApiResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        if not request.url.path.startswith("/api"):
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk
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
    app.add_middleware(ApiResponseMiddleware)
    register_routes(app)

    @app.on_event("startup")
    def on_startup():
        create_db_and_tables()

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, e: HTTPException):
        try:
            name = HTTPStatus(e.status_code).phrase
        except Exception:
            name = "HTTP Error"
        payload = {
            "success": False,
            "error": {
                "code": e.code,
                "name": name,
                "message": e.description,
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
