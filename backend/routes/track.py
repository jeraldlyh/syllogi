from flask import Blueprint, request
from werkzeug.exceptions import BadRequest

from lib.track import _find_track

bp = Blueprint("track", __name__)


@bp.get("/")
def find_track():
    artist_name = request.args.get("artist_name")
    title = request.args.get("title")

    if not artist_name:
        raise BadRequest(description="artist_name is required")
    if not title:
        raise BadRequest(description="title is required")

    return _find_track(artist_name, title)
