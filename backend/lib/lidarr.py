import os
import requests
from difflib import SequenceMatcher

from typing import List
from lib.utils import dump_results, get_clean_name

LIDARR_BASE_URL = os.getenv("LIDARR_BASE_URL")
LIDARR_API_KEY = os.getenv("LIDARR_API_KEY")


def _lidarr(
    path: str,
    *,
    method: str = "GET",
    params: dict | None = None,
    json: dict | list | None = None,
    data: dict | str | bytes | None = None,
    timeout: float = 30.0,
) -> dict:
    headers = {"X-Api-Key": LIDARR_API_KEY}

    response = requests.request(
        method.upper(),
        f"{LIDARR_BASE_URL}/api/v1{path}",
        headers=headers,
        params=params,
        json=json,
        data=data,
        timeout=timeout,
    )
    response.raise_for_status()

    return response.json()


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


def get_lidarr_track_metadata(trackfile_id: str) -> dict:
    return _lidarr(f"/trackfile/{trackfile_id}")
