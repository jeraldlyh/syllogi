from flask import Blueprint, current_app, jsonify, request

from lib.jellyfin import (
    _get_jellyfin_playlists,
    _add_songs_to_jellyfin_playlist,
    _get_jellyfin_user_by_name,
    _create_jellyfin_playlist,
    _get_jellyfin_playlist_songs,
    _delete_songs_from_jellyfin_playlist,
)
from lib.spotify import _get_songs_by_playlist, _get_playlist
from lib.track import _find_track
from lib.utils import dump_results

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
    songs = _get_songs_by_playlist(playlist_id=playlist_id)
    user = _get_jellyfin_user_by_name(username=username)

    jellyfin_songs = []
    for song in songs:
        artist_name = song["itemV2"]["data"]["albumOfTrack"]["artists"]["items"][0][
            "profile"
        ]["name"]
        album_song_name = song["itemV2"]["data"]["albumOfTrack"]["name"]

        track = _find_track(artist_name=artist_name, track_name=album_song_name)
        if not track.get("track").get("id"):
            current_app.logger.info(f"{artist_name} - {album_song_name}: RETRYING")
            album_song_name = song["itemV2"]["data"]["name"]
            track = _find_track(artist_name=artist_name, track_name=album_song_name)

        if track.get("track").get("id"):
            current_app.logger.info(f"{artist_name} - {album_song_name}: OK")
            jellyfin_songs.append(track)
        else:
            current_app.logger.warning(f"{artist_name} - {album_song_name}: MISSING")

    if len(jellyfin_songs) > 0:
        spotify_playlist_name = spotify_playlist["data"]["playlistV2"]["name"]
        jellyfin_user_id = user.get("Id")
        jellyfin_playlists = _get_jellyfin_playlists(user_id=jellyfin_user_id)

        existing_playlist = next(
            (
                playlist
                for playlist in jellyfin_playlists
                if spotify_playlist_name == playlist.get("Name")
            ),
            {},
        )

        existing_playlist_id = existing_playlist.get("Id")

        if not existing_playlist_id:
            new_playlist = _create_jellyfin_playlist(
                playlist_name=spotify_playlist_name, user_id=jellyfin_user_id
            )
            existing_playlist_id = new_playlist.get("Id")

        existing_songs = _get_jellyfin_playlist_songs(
            playlist_id=existing_playlist_id, user_id=jellyfin_user_id
        )
        existing_track_ids = [track.get("Id") for track in existing_songs]
        jellyfin_track_ids = [track["track"]["id"] for track in jellyfin_songs]

        new_track_ids = list(set(jellyfin_track_ids) - set(existing_track_ids))
        outdated_track_ids = list(set(existing_track_ids) - set(jellyfin_track_ids))

        if len(new_track_ids) > 0:
            current_app.logger.info(
                f"Adding {len(new_track_ids)} songs to {spotify_playlist_name} playlist"
            )
            _add_songs_to_jellyfin_playlist(
                playlist_id=existing_playlist_id,
                user_id=jellyfin_user_id,
                track_ids=new_track_ids,
            )

        if len(outdated_track_ids) > 0:
            current_app.logger.info(
                f"Deleting {len(outdated_track_ids)} songs from {spotify_playlist_name} playlist"
            )
            _delete_songs_from_jellyfin_playlist(
                playlist_id=existing_playlist_id, track_ids=outdated_track_ids
            )
    return jellyfin_songs
