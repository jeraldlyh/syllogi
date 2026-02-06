from flask import Blueprint, jsonify, request
from lib.track import _find_track

bp = Blueprint("track", __name__)


@bp.get("/")
def find_track():
    artist_name = request.args.get("artist_name")
    title = request.args.get("title")

    if not artist_name:
        return jsonify(error="artist_name is required"), 400
    if not title:
        return jsonify(error="title is required"), 400

    return _find_track(artist_name, title)
