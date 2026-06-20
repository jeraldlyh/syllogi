import logging
from collections.abc import Callable, Hashable
from typing import Any, TypeVar

import httpx

from lib.models.lastfm import (
    LastFMChartTrack,
    LastFMRecentTrack,
    LastFMSimilarTrack,
    LastFMTopTrack,
)
from lib.env import get_environment_variable


logger = logging.getLogger(__name__)
T = TypeVar("T", bound=Hashable)


async def _lastfm(
    path: str = "",
    method: str = "GET",
    params: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    json: dict[str, Any] | list[Any] | None = None,
    data: dict[str, Any] | None = None,
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

    async with httpx.AsyncClient() as client:
        response = await client.request(
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


def _get_nested_value(data: Any, path: str) -> Any:
    value: Any = data

    for key in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


async def _get_lastfm_tracks_paginated(
    *,
    params: dict[str, Any],
    limit: int,
    response_path: str,
    track_factory: Callable[[dict[str, Any]], T],
    track_filter: Callable[[dict[str, Any]], bool] | None = None,
) -> list[T]:
    """Helper for fetching paginated track data from LastFM.

    Args:
        params: Base query parameters for the LastFM API request (excluding pagination).
        limit: Maximum number of tracks to return.
        response_path: Dot-separated path to the list of tracks in the API response (e.g. "recenttracks.track").
        track_factory: Callable that converts a raw track dict from the API response into an instance of T.
        track_filter: Optional callable that filters raw track dicts from the API response before conversion. If provided, only tracks for which this returns True will be included.
    """

    page = 1
    total_pages: int | None = None
    tracks: list[T] = []
    seen: set[T] = set()
    response_root_key, _, response_tracks_key = response_path.rpartition(".")

    while len(tracks) < limit:
        data = await _lastfm(
            params={
                **params,
                "limit": limit,
                "page": page,
            },
        )
        response_data = _get_nested_value(data, response_root_key) or {}
        raw_tracks = response_data.get(response_tracks_key, [])

        if not raw_tracks:
            break

        for raw_track in raw_tracks:
            if track_filter is not None and not track_filter(raw_track):
                continue

            track = track_factory(raw_track)
            if track in seen:
                continue

            seen.add(track)
            tracks.append(track)

            if len(tracks) >= limit:
                break

        if total_pages is None:
            metadata = response_data.get("@attr", {})
            total_pages_raw = metadata.get("totalPages")

            if total_pages_raw:
                total_pages = int(total_pages_raw)

        if total_pages is not None and page >= total_pages:
            break

        if len(raw_tracks) < limit:
            break

        page += 1
    return tracks


async def verify_lastfm_username(username: str) -> bool:
    """Verify that a Last.fm username exists."""

    try:
        data = await _lastfm(
            params={"user": username, "method": "user.getInfo"},
        )
        return "user" in data
    except Exception:
        return False


async def get_lastfm_recent_tracks(
    user: str, limit: int = 30
) -> list[LastFMRecentTrack]:
    return await _get_lastfm_tracks_paginated(
        params={
            "user": user,
            "method": "user.getRecentTracks",
        },
        limit=limit,
        response_path="recenttracks.track",
        track_filter=lambda track: track.get("mbid", "") != "",
        track_factory=lambda track: LastFMRecentTrack(
            artist_name=track.get("artist", {}).get("#text", ""),
            track_name=track.get("name", ""),
            album_name=track.get("album", {}).get("#text", ""),
            musicbrainz_id=track.get("mbid", ""),
        ),
    )


async def get_lastfm_top_tracks(
    user: str, period: str = "6month", limit: int = 30
) -> list[LastFMTopTrack]:
    return await _get_lastfm_tracks_paginated(
        params={
            "user": user,
            "method": "user.getTopTracks",
            "period": period,
        },
        limit=limit,
        response_path="toptracks.track",
        track_filter=lambda track: track.get("mbid", "") != "",
        track_factory=lambda track: LastFMTopTrack(
            artist_name=track.get("artist", {}).get("name", ""),
            track_name=track.get("name", ""),
            duration=track.get("duration", 0),
            musicbrainz_id=track.get("mbid", ""),
            playcount=track.get("playcount", 0),
        ),
    )


async def get_lastfm_similar_tracks(
    user: str, artist: str, track: str
) -> list[LastFMSimilarTrack]:
    data = await _lastfm(
        params={
            "user": user,
            "method": "track.getSimilar",
            "artist": artist,
            "track": track,
        },
    )
    raw_tracks = _get_nested_value(data, "similartracks.track") or []
    tracks: list[LastFMSimilarTrack] = []

    for raw_track in raw_tracks:
        if raw_track.get("mbid", "") == "":
            continue

        tracks.append(
            LastFMSimilarTrack(
                artist_name=raw_track.get("artist", {}).get("name", ""),
                track_name=raw_track.get("name", ""),
                duration=raw_track.get("duration", 0),
                musicbrainz_id=raw_track.get("mbid", ""),
                playcount=raw_track.get("playcount", 0),
                similarity_score=raw_track.get("match", 0.0),
            )
        )
    return tracks


async def get_lastfm_chart_top_tracks(limit: int = 50) -> list[LastFMChartTrack]:
    data = await _lastfm(
        params={
            "method": "chart.getTopTracks",
            "limit": limit,
        },
    )
    raw_tracks = _get_nested_value(data, "tracks.track") or []
    tracks: list[LastFMChartTrack] = []

    for raw_track in raw_tracks:
        images = raw_track.get("image", [])
        image_url = next(
            (img["#text"] for img in reversed(images) if img.get("#text")),
            "",
        )
        tracks.append(
            LastFMChartTrack(
                artist_name=raw_track.get("artist", {}).get("name", ""),
                track_name=raw_track.get("name", ""),
                duration=int(raw_track.get("duration", 0) or 0),
                listeners=int(raw_track.get("listeners", 0) or 0),
                playcount=int(raw_track.get("playcount", 0) or 0),
                musicbrainz_id=raw_track.get("mbid", ""),
                image_url=image_url,
            )
        )

    return tracks
