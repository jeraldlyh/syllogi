from flask import Blueprint, current_app

from lib.spotify import get_songs_by_playlist
from lib.track import _find_track
from lib.utils import dump_results

bp = Blueprint("spotify", __name__)


@bp.get("/import/<id>")
def import_playlist(id: str):
    songs = get_songs_by_playlist(id)
    tracks = []
    for song in songs:
        artist_name = song["itemV2"]["data"]["albumOfTrack"]["artists"]["items"][0][
            "profile"
        ]["name"]
        album_song_name = song["itemV2"]["data"]["albumOfTrack"]["name"]

        track = _find_track(artist_name=artist_name, title=album_song_name)
        if not track.get("track").get("id"):
            current_app.logger.info(f"{artist_name} - {album_song_name}: RETRYING")
            album_song_name = song["itemV2"]["data"]["name"]
            track = _find_track(artist_name=artist_name, title=album_song_name)

        if not track.get("track").get("id"):
            current_app.logger.info(f"{artist_name} - {album_song_name}: OK")
        else:
            current_app.logger.warning(f"{artist_name} - {album_song_name}: MISSING")
        tracks.append(track)
    dump_results("result", tracks)
