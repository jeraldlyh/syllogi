import logging
from typing import Any

import requests

from lib.models.lastfm import LastFMRecentTrack, LastFMSimilarTrack, LastFMTopTrack
from lib.env import get_environment_variable


logger = logging.getLogger(__name__)


def _lastfm(
    path: str = "",
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
    api_key = get_environment_variable("LASTFM_API_KEY", ignore_error=False)
    api_url = get_environment_variable("LASTFM_URL", ignore_error=False)

    default_params = {
        "api_key": api_key,
        "format": "json",
    }
    default_params.update(params or {})

    response = requests.request(
        method=method.upper(),
        url=f"{api_url}{path}",
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


def get_lastfm_recent_tracks(user: str, limit: int = 30) -> list[LastFMRecentTrack]:
    page = 1
    total_pages: int | None = None
    tracks: list[LastFMRecentTrack] = []
    seen: set[LastFMRecentTrack] = set()

    while len(tracks) < limit:
        data = _lastfm(
            params={
                "user": user,
                "method": "user.getRecentTracks",
                "limit": limit,
                "page": page,
            },
        )
        recent_tracks = data.get("recenttracks", {})
        raw_tracks = recent_tracks.get("track", [])

        if not raw_tracks:
            break

        for track in raw_tracks:
            recent_track = LastFMRecentTrack(
                artist_name=track["artist"]["#text"],
                track_name=track["name"],
                album_name=track["album"]["#text"],
                musicbrainz_id=track["mbid"],
            )
            if recent_track in seen:
                continue

            seen.add(recent_track)
            tracks.append(recent_track)

            if len(tracks) >= limit:
                break

        if total_pages is None:
            metadata = recent_tracks.get("@attr", {}) or {}
            total_pages_raw = metadata.get("totalPages")

            if total_pages_raw:
                total_pages = int(total_pages_raw)

        if total_pages is not None and page >= total_pages:
            break

        if len(raw_tracks) < limit:
            break
        page += 1
    return tracks


def get_lastfm_top_tracks(user: str, period="6month", limit=30) -> list[LastFMTopTrack]:
    data = _lastfm(
        params={
            "user": user,
            "method": "user.getTopTracks",
            "period": period,
            "limit": limit,
        },
    )
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


def get_lastfm_similar_tracks(
    user: str, artist: str, track: str, limit=5
) -> list[LastFMSimilarTrack]:
    data = _lastfm(
        params={
            "user": user,
            "method": "track.getSimilar",
            "artist": artist,
            "track": track,
            "limit": limit,
        },
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
        if "mbid" in track
    ]
