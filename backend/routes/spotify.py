from flask import Blueprint, current_app, jsonify, request

from lib.jellyfin import (
    _get_jellyfin_playlists,
    _get_jellyfin_users,
    _get_jellyfin_user_by_name,
    _create_jellyfin_playlist,
)
from lib.spotify import _get_songs_by_playlist, _get_playlist
from lib.track import _find_track

bp = Blueprint("spotify", __name__)


@bp.get("/<id>")
def get_playlist(id: str) -> dict:
    return _get_playlist(id)


@bp.post("/import")
def import_playlist():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    body = request.get_json()
    playlist_id = body.get("id")
    username = body.get("username")

    if not playlist_id:
        return jsonify(error="id is required"), 400

    if not username:
        return jsonify(error="username is required"), 400

    spotify_playlist = _get_playlist(playlist_id=playlist_id)
    songs = _get_songs_by_playlist(spotify_playlist)
    user = _get_jellyfin_user_by_name(username=username)

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

    if len(tracks) > 0:
        spotify_playlist_name = spotify_playlist["data"]["playlistV2"]["name"]
        jellyfin_user_id = user.get("Id")
        jellyfin_playlists = _get_jellyfin_playlists(user_id=jellyfin_user_id)

        existing_playlist = next(
            (
                playlist
                for playlist in jellyfin_playlists["Items"]
                if spotify_playlist_name == playlist.get("Name")
            ),
            {},
        )

        existing_playlist_id = existing_playlist.get("id")

        if not existing_playlist_id:
            existing_playlist_id = _create_jellyfin_playlist(
                playlist_name=spotify_playlist_name, user_id=jellyfin_user_id
            )
    return tracks
