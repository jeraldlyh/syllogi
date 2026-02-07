import os
from flask import Flask
from routes import register_routes
from logging.config import dictConfig
from dotenv import load_dotenv

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

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
db = SQLAlchemy()
migrate = Migrate()


def get_connection_string() -> str:
    username = os.getenv("DATABASE_USERNAME")
    password = os.getenv("DATABASE_PASSWORD")
    url = os.getenv("DATABASE_URL")
    name = os.getenv("DATABASE_NAME")

    if username and password and url and name:
        return f"postgresql://{username}:{password}@{url}/${name}"
    return "postgresql://syllogi:syllogi@localhost:5432/syllogi"


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = get_connection_string()
    db.init_app(app)
    migrate.init_app(app, db)
    return app


app = create_app()
register_routes(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
