from flask import Flask
from routes.health import bp as health_bp
from routes.track import bp as track_bp
from routes.user import bp as user_bp
from routes.spotify import bp as spotify_bp


def register_routes(app: Flask) -> None:
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(track_bp, url_prefix="/api/track")
    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(spotify_bp, url_prefix="/api/spotify")
