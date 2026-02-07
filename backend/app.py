import os
from logging.config import dictConfig

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_migrate import Migrate
from werkzeug.exceptions import HTTPException

from models.db import db
from routes import register_routes

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s [%(module)s]: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)

load_dotenv()
migrate = Migrate()


def get_connection_string() -> str:
    username = os.getenv("DATABASE_USERNAME")
    password = os.getenv("DATABASE_PASSWORD")
    url = os.getenv("DATABASE_URL")
    name = os.getenv("DATABASE_NAME")

    if username and password and url and name:
        return f"postgresql://{username}:{password}@{url}/{name}"
    return "postgresql://syllogi:syllogi@localhost:5432/syllogi"


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = get_connection_string()
    db.init_app(app)
    migrate.init_app(app, db)

    register_routes(app)

    @app.errorhandler(HTTPException)
    def _handle_http_error(e: HTTPException):
        payload = {
            "success": False,
            "error": {
                "code": e.code,
                "name": e.name,
                "message": e.description,
            },
        }
        response = jsonify(payload)
        response.status_code = e.code
        return response

    @app.errorhandler(Exception)
    def _handle_unexpected_error(e: Exception):
        app.logger.exception("Unhandled exception")
        payload = {
            "success": False,
            "error": {
                "code": 500,
                "name": "Internal Server Error",
                "message": "Something went wrong",
            },
        }
        response = jsonify(payload)
        response.status_code = 500
        return response

    @app.after_request
    def _format_response(response):
        if not request.path.startswith("/api"):
            return response

        data = (
            response.get_json(silent=True)
            if response.is_json
            else response.get_data(as_text=True)
        )
        if isinstance(data, dict) and any(
            k in data for k in ("success", "error", "data")
        ):
            return response

        envelope = {"success": 200 <= response.status_code < 300, "data": data}
        response = jsonify(envelope)
        response.status_code = response.status_code

        for k, v in response.headers.items():
            if k.lower() not in ("content-length", "content-type"):
                response.headers[k] = v
        return response

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
