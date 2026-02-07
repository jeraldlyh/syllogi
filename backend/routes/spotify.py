import os
import time

from flask import Blueprint, current_app, request
from werkzeug.exceptions import BadRequest, UnsupportedMediaType, NotFound

from lib.jellyfin import (
    _add_songs_to_jellyfin_playlist,
    _create_jellyfin_playlist,
    _delete_songs_from_jellyfin_playlist,
    _get_jellyfin_playlist_songs,
    _get_jellyfin_playlists,
    _get_jellyfin_user_by_name,
    _update_jellyfin_playlist_image,
)
from lib.notification import _send_discord_notification
from lib.spotify import _get_playlist, _get_songs_by_playlist
from lib.track import _find_track
from lib.utils import _convert_seconds_to_readable_time

bp = Blueprint("spotify", __name__)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")


@bp.get("/<id>")
def get_playlist(id: str) -> dict:
    return _get_playlist(id)


@bp.post("/import")
def import_playlist():
    if not request.is_json:
        raise UnsupportedMediaType(description="Content-Type must be application/json")
    body = request.get_json()
    playlist_id = body.get("id")
    username = body.get("username")

    if not playlist_id:
        raise BadRequest(description="playlist_id is required")

    if not username:
        raise BadRequest(description="username is required")

    start = time.time()
    spotify_playlist = _get_playlist(playlist_id=playlist_id)
    songs = _get_songs_by_playlist(playlist_id=playlist_id)
    user = _get_jellyfin_user_by_name(username=username)

    if not user:
        raise NotFound(description=f"Unable to find username: {username}")

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

    num_of_new_tracks, num_of_outdated_tracks = 0, 0

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

        num_of_new_tracks = len(new_track_ids)
        num_of_outdated_tracks = len(outdated_track_ids)

        if num_of_new_tracks > 0:
            current_app.logger.info(
                f"Adding {num_of_new_tracks} songs to {spotify_playlist_name} playlist"
            )
            _add_songs_to_jellyfin_playlist(
                playlist_id=existing_playlist_id,
                user_id=jellyfin_user_id,
                track_ids=new_track_ids,
            )

        if num_of_outdated_tracks > 0:
            current_app.logger.info(
                f"Deleting {num_of_outdated_tracks} songs from {spotify_playlist_name} playlist"
            )
            _delete_songs_from_jellyfin_playlist(
                playlist_id=existing_playlist_id, track_ids=outdated_track_ids
            )

    spotify_playlist_thumbnail_metadata = max(
        spotify_playlist["data"]["playlistV2"]["ownerV2"]["data"]["avatar"]["sources"],
        key=lambda x: x.get("height"),
    )
    spotify_playlist_thumbnail_url = spotify_playlist_thumbnail_metadata.get("url")
    _update_jellyfin_playlist_image(
        playlist_id=playlist_id,
        image_url=spotify_playlist_thumbnail_url
        if spotify_playlist_thumbnail_url.endswith((".png", "jpg", "jpeg"))
        else None,
    )
    end = time.time()

    _send_discord_notification(
        DISCORD_WEBHOOK_URL,
        title="Import Summary",
        fields=[
            {"name": "Username", "value": username, "inline": True},
            {"name": "Playlist", "value": spotify_playlist_name, "inline": True},
            {
                "name": "New/Outdated Tracks(s)",
                "value": f"{num_of_new_tracks} 🔺 {num_of_outdated_tracks} 🔻",
                "inline": True,
            },
            {
                "name": "Missing Tracks(s)",
                "value": len(songs) - len(jellyfin_track_ids),
                "inline": True,
            },
            {
                "name": "Total Tracks(s)",
                "value": len(songs),
                "inline": True,
            },
            {
                "name": "Time Taken",
                "value": _convert_seconds_to_readable_time(seconds=end - start),
                "inline": True,
            },
        ],
        timestamp=True,
    )

    return jellyfin_songs
