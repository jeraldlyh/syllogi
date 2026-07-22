import logging
from typing import Any

from fastapi import HTTPException, status
import httpx

from lib.env import get_environment_variable
from lib.models.common import RecommendationTrack
from lib.providers.recommendation.base import RecommendationSourceProvider

logger = logging.getLogger(__name__)


class ListenBrainzRecommendationProvider(RecommendationSourceProvider):
    """Recommendation source backed by the ListenBrainz API."""

    async def _listenbrainz(
        self,
        path: str,
        *,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> Any:
        """HTTP helper for the ListenBrainz API."""

        api_url = str(get_environment_variable("LISTENBRAINZ_URL", ignore_error=False))
        api_key = str(
            get_environment_variable("LISTENBRAINZ_API_KEY", ignore_error=False)
        )

        headers: dict[str, str] = {
            "Authorization": f"Token {api_key}",
        }

        request_url = f"{api_url.rstrip('/')}{path}"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method.upper(),
                url=request_url,
                headers=headers,
                params=params,
                json=json,
                timeout=timeout,
            )

        if response.status_code == 404:
            return None
        response.raise_for_status()

        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    async def verify_username(self, username: str) -> bool:
        """Verify that a ListenBrainz username exists."""

        try:
            data = await self._listenbrainz(
                f"/1/user/{username}/listen-count",
            )
            return data is not None and "payload" in data
        except httpx.HTTPStatusError as e:
            logger.debug(f"HTTP error: {e}")
        except httpx.RequestError as e:
            logger.warning(f"Request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        return False

    async def get_recent_tracks(
        self, *, username: str, limit: int = 30
    ) -> list[RecommendationTrack]:
        data = await self._listenbrainz(
            f"/1/user/{username}/listens",
            params={"count": limit},
        )

        if not data or "payload" not in data:
            return []

        tracks = data["payload"].get("listens", [])
        seen: set[tuple[str, str]] = set()
        result: list[RecommendationTrack] = []

        for track in tracks:
            track_info = track.get("track_metadata", {})
            artist = track_info.get("artist_name", "")
            name = track_info.get("track_name", "")
            mbid = track_info.get("mbid_mapping", {}).get("recording_mbid", "")
            key = (artist, name)

            if key in seen or not name:
                continue

            seen.add(key)
            result.append(
                RecommendationTrack(
                    artist_name=artist,
                    track_name=name,
                    musicbrainz_id=mbid,
                    album_name=track_info.get("release_name", ""),
                    duration=track_info.get("additional_info", {}).get("duration_ms", 0)
                    / 1000,
                    playcount=0,
                    similarity_score=0.0,
                    year="",
                )
            )
        return result

    async def get_top_tracks(
        self, *, username: str, period: str = "7day", limit: int = 30
    ) -> list[RecommendationTrack]:
        range_map = {
            "7day": "week",
            "1month": "month",
            "3month": "quarter",
            "6month": "half_yearly",
            "1year": "year",
        }

        if period not in range_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid period",
            )

        data = await self._listenbrainz(
            f"/1/stats/user/{username}/recordings",
            params={"count": limit, "range": period},
        )

        if not data or "payload" not in data:
            return []

        tracks = data["payload"].get("recordings", [])

        return [
            RecommendationTrack(
                artist_name=track.get("artist_name", ""),
                track_name=track.get("track_name", ""),
                musicbrainz_id=track.get("recording_mbid", ""),
                album_name=track.get("release_name", ""),
                duration=0,
                playcount=track.get("listen_count", 0),
                similarity_score=0.0,
                year="",
            )
            for track in tracks
            if track.get("track_name") and track.get("artist_name")
        ]

    async def get_similar_tracks(
        self,
        *,
        artist_name: str,
        track_name: str,
        musicbrainz_id: str = "",
        count: int = 10,
    ) -> list[RecommendationTrack]:
        """Get tracks similar to a given track using ListenBrainz LB Radio.

        Uses the similar-artist endpoint to discover tracks from artists
        similar to the seed track's artist. Requires resolving the artist
        MBID first via the metadata lookup endpoint.
        """

        lookup_data = await self._listenbrainz(
            "/1/metadata/lookup/",
            params={
                "artist_name": artist_name,
                "recording_name": track_name,
                "count": count,
            },
        )

        if not lookup_data:
            return []

        artist_mbid = (
            lookup_data.get("artist_mbids", [])[0]
            if lookup_data.get("artist_mbids")
            else None
        )

        if not artist_mbid:
            return []

        tracks = await self._listenbrainz(
            f"/1/lb-radio/artist/{artist_mbid}",
            params={
                "mode": "medium",
                "max_similar_artists": 1,
                "max_recordings_per_artist": 1,
                "pop_begin": 0,
                "pop_end": 100,
            },
        )

        if not tracks:
            return []

        results = []

        for artist_mbid in tracks:
            for artist_data in tracks[artist_mbid]:
                recording_mbid = artist_data.get("recording_mbid", "")

                if not recording_mbid:
                    continue

                track = await self._listenbrainz(
                    "/1/metadata/recording/",
                    params={"recording_mbids": recording_mbid, "inc": "release"},
                )
                track_metadata = next(iter(track.values()), None) if track else None

                if not track_metadata:
                    continue

                release = track_metadata.get("release", {})

                results.append(
                    RecommendationTrack(
                        artist_name=release.get("album_artist_name", ""),
                        track_name=track_metadata.get("recording", {}).get("name", ""),
                        musicbrainz_id=recording_mbid,
                        album_name=release.get("name", ""),
                        duration=track_metadata.get("recording", {}).get("length", 0)
                        / 1000,
                        playcount=0,
                        similarity_score=0.0,
                        year=str(track_metadata.get("year", "")),
                    )
                )
        return results
