import logging
import os
from typing import Any

import requests

from lib.common import LastFMRecentTrack, LastFMSimilarTrack, LastFMTopTrack

LASTFM_API_KEY = "http://ws.audioscrobbler.com/2.0"
LASTFM_BASE_URL = os.getenv("LASTFM_BASE_URL")

logger = logging.getLogger(__name__)


def _lastfm(
    path: str,
    *,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    json: dict[str, Any] | list[Any] | None = None,
    data: dict[str, Any] | str | bytes | None = None,
    timeout: float = 30.0,
) -> Any:
    base_headers = {
        "Content-Type": "application/json",
    }
    default_params = {
        "api_key": LASTFM_API_KEY,
        "format": "json",
    }
    default_params.update(params or {})

    response = requests.request(
        method=method.upper(),
        url=f"{LASTFM_BASE_URL}{path}",
        headers={**base_headers, **(headers or {})},
        params={**default_params},
        json=json,
        data=data,
        timeout=timeout,
    )
    response.raise_for_status()

    if response.status_code == 204 or not response.content:
        return None
    return response.json()


def get_recent_tracks(user: str, limit=30) -> list[LastFMRecentTrack]:
    data = _lastfm("user.getRecentTracks", params={"user": user, "limit": limit})
    tracks = data.get("recenttracks", {}).get("track", [])

    return [
        LastFMRecentTrack(
            artist_name=track["artist"]["#text"],
            track_name=track["name"],
            album_name=track["album"]["#text"],
            musicbrainz_id=track["mbid"],
        )
        for track in tracks
    ]


def get_top_tracks(user: str, limit=30) -> list[LastFMTopTrack]:
    data = _lastfm("user.getTopTracks", params={"user": user, "limit": limit})
    tracks = data.get("toptracks", {}).get("track", [])

    return [
        LastFMTopTrack(
            artist_name=track["artist"]["name"],
            track_name=track["name"],
            duration=track["duration"],
            musicbrainz_id=track["mbid"],
            playcount=track["playcount"],
        )
        for track in tracks
    ]


def get_similar_tracks(
    user: str, artist: str, track: str, limit=10
) -> list[LastFMSimilarTrack]:
    data = _lastfm(
        "user.getTopTracks",
        params={"user": user, "artist": artist, "track": track, "limit": limit},
    )
    tracks = data.get("similartracks", {}).get("track", [])

    return [
        LastFMSimilarTrack(
            artist_name=track["artist"]["name"],
            track_name=track["name"],
            duration=track["duration"],
            musicbrainz_id=track["mbid"],
            playcount=track["playcount"],
            similarity_score=track["match"],
        )
        for track in tracks
    ]
