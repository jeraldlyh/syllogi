import logging
from collections.abc import Callable, Hashable
from typing import Any, TypeVar

import httpx

from lib.models.lastfm import LastFMRecentTrack, LastFMSimilarTrack, LastFMTopTrack
from lib.env import get_environment_variable


logger = logging.getLogger(__name__)
T = TypeVar("T", bound=Hashable)


async def _lastfm(
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
    page = 1
    total_pages: int | None = None
    tracks: list[T] = []
    seen: set[T] = set()
    response_root_key, _, response_tracks_key = response_path.rpartition(".")

    while len(tracks) < limit:
        logger.debug(f"Fetching LastFM tracks: page {page}, limit {limit}")
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
    user: str, artist: str, track: str, limit: int = 5
) -> list[LastFMSimilarTrack]:
    return await _get_lastfm_tracks_paginated(
        params={
            "user": user,
            "method": "track.getSimilar",
            "artist": artist,
            "track": track,
        },
        limit=limit,
        response_path="similartracks.track",
        track_filter=lambda track: track.get("mbid", "") != "",
        track_factory=lambda track: LastFMSimilarTrack(
            artist_name=track.get("artist", {}).get("name", ""),
            track_name=track.get("name", ""),
            duration=track.get("duration", 0),
            musicbrainz_id=track.get("mbid", ""),
            playcount=track.get("playcount", 0),
            similarity_score=track.get("match", 0.0),
        ),
    )
