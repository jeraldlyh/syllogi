import json
import logging
import sys
import os
import requests
import re
import unicodedata
from difflib import SequenceMatcher

from typing import List
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(BASE_DIR, "SpotAPI"))

from spotapi.playlist import PublicPlaylist
from spotapi.album import PublicAlbum

load_dotenv()

JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY")
JELLYFIN_BASE_URL = os.getenv("JELLYFIN_BASE_URL")
LIDARR_BASE_URL = os.getenv("LIDARR_BASE_URL")
LIDARR_API_KEY = os.getenv("LIDARR_API_KEY")


def get_logger():
    logger = logging.getLogger("spotapi")
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)

    logger.addHandler(ch)

    return logger


logger = get_logger()


def get_songs_by_playlist(playlist_id: str) -> List[dict]:
    offset = 0
    limit = 50
    songs = []

    playlist = PublicPlaylist(playlist_id)
    playlist_info = playlist.get_playlist_info(limit=limit)

    while offset < playlist_info["data"]["playlistV2"]["content"]["totalCount"]:
        songs.extend(playlist_info["data"]["playlistV2"]["content"]["items"])
        offset += limit
        playlist_info = playlist.get_playlist_info(offset=offset, limit=limit)
        logger.info(f"Fetched {len(songs)} songs...")

    logger.info(f"Total songs fetched: {len(songs)}")

    return songs


def get_album_by_id(album_id: str) -> dict:
    album = PublicAlbum(album_id)
    album_info = album.get_album_info()

    return album_info


def get_clean_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    # NOTE: Temporarily removing this for chinese songs
    # non_ascii = normalized.encode("ascii", "ignore").decode("ascii")
    non_symbols = re.compile(r"[^a-z0-9]+").sub("", normalized.casefold())

    return non_symbols


def _jellyfin(path: str, **params) -> dict:
    headers = {"X-Emby-Token": JELLYFIN_API_KEY}
    response = requests.get(
        f"{JELLYFIN_BASE_URL}/{path}", headers=headers, params=params
    )
    response.raise_for_status()

    return response.json()


def _lidarr(path: str, **params) -> dict:
    headers = {"X-Api-Key": LIDARR_API_KEY}
    response = requests.get(
        f"{LIDARR_BASE_URL}/api/v1{path}", headers=headers, params=params
    )
    response.raise_for_status()

    return response.json()


def get_jellyfin_artist(name: str) -> dict:
    return _jellyfin(f"/Artists/{name}")


def dump_results(file_name: str, data: dict) -> None:
    with open(f"{file_name}.json", "w") as file:
        json.dump(data, file, indent=4)


def get_potential_lidarr_songs(track_name: str, artist_id: str) -> List[dict]:
    tracks = _lidarr("/track", artistId=artist_id)
    albums = _lidarr("/album", artistId=artist_id)

    dump_results("tracks", tracks)

    candidates = []
    for track in tracks:
        lidarr_track_name = track.get("title")
        lidarr_clean_track_name = get_clean_name(lidarr_track_name)
        clean_track_name = get_clean_name(track_name)

        album_name = next(
            album.get("title")
            for album in albums
            if album.get("id") == track.get("albumId")
        )

        if album_name:
            track["album_name"] = album_name

        if lidarr_track_name.casefold() == track_name.casefold():
            candidates.append(track)
            continue

        score = max(
            SequenceMatcher(None, lidarr_clean_track_name, clean_track_name).ratio(),
            SequenceMatcher(
                None, lidarr_track_name.casefold(), track_name.casefold()
            ).ratio(),
        )

        if score >= 0.9:
            candidates.append(track)
            continue

        # NOTE: Might possibly increase matching capabilities if album name is appended to the track name
        #
        # if not album_name:
        #     continue
        #
        # lidarr_track_name_with_album = f"{lidarr_track_name} ({album_name})"
        # lidarr_clean_track_name_with_album = get_clean_name(
        #     lidarr_track_name_with_album
        # )
        # score = max(
        #     SequenceMatcher(
        #         None, lidarr_clean_track_name_with_album, clean_track_name
        #     ).ratio(),
        #     SequenceMatcher(
        #         None, lidarr_track_name_with_album.casefold(), track_name.casefold()
        #     ).ratio(),
        # )
        #
        # if score >= 0.9:
        #     candidates.append(track)

    return candidates


def get_lidarr_artist(name: str) -> str:
    artists = _lidarr("/artist")
    # dump_results("artist", artists)

    best_match, best_score = None, 0.0

    for artist in artists:
        lidarr_artist_name = artist.get("artistName")
        lidarr_artist_clean_name = artist.get("cleanName")
        clean_name = get_clean_name(name)

        if (
            lidarr_artist_clean_name == clean_name
            or lidarr_artist_name.casefold() == name.casefold()
        ):
            return artist
        score = max(
            SequenceMatcher(None, lidarr_artist_clean_name, clean_name).ratio(),
            SequenceMatcher(
                None, lidarr_artist_name.casefold(), name.casefold()
            ).ratio(),
        )

        if score > best_score and score >= 0.9:
            best_match = artist
            best_score = score

    return None if not best_match else best_match


def find_track(artist_name: str, title: str) -> dict:
    empty_result = {
        "artist_name": artist_name,
        "track": {"name": None, "id": None, "file_id": None},
        "album": {"name": None, "id": None},
        "search_name": title,
        "exists": False,
        "path": None,
        "quality": None,
    }

    artist = get_lidarr_artist(artist_name)

    if not artist:
        return empty_result

    artist_id = artist.get("id")
    candidates = get_potential_lidarr_songs(title, artist_id)

    for candidate in candidates:
        if candidate.get("hasFile") and candidate.get("trackFileId"):
            file_meta = _lidarr(f"/trackfile/{candidate.get('trackFileId')}")

            return {
                "artist_name": artist_name,
                "track": {
                    "id": candidate.get("id"),
                    "name": candidate.get("title"),
                    "file_id": candidate.get("trackFileId"),
                },
                "album": {
                    "id": candidate.get("id"),
                    "name": candidate.get("album_name"),
                },
                "search_name": title,
                "exists": True,
                "path": file_meta.get("path"),
                "quality": file_meta.get("quality"),
            }
    return empty_result


songs = get_songs_by_playlist(os.getenv("SPOTIFY_PLAYLIST"))
dump_results("spotify", songs)

tracks = []
for song in songs:
    artist_name = song["itemV2"]["data"]["albumOfTrack"]["artists"]["items"][0][
        "profile"
    ]["name"]
    album_song_name = song["itemV2"]["data"]["albumOfTrack"]["name"]

    track = find_track(artist_name=artist_name, title=album_song_name)
    if not track.get("track").get("id"):
        logger.info(f"{artist_name} - {album_song_name}: RETRYING")
        album_song_name = song["itemV2"]["data"]["name"]
        track = find_track(artist_name=artist_name, title=album_song_name)

    if not track.get("track").get("id"):
        logger.info(f"{artist_name} - {album_song_name}: OK")
    else:
        logger.warning(f"{artist_name} - {album_song_name}: MISSING")
    tracks.append(track)
dump_results("result", tracks)
