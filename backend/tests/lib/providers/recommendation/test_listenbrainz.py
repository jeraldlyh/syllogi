import httpx
import pytest
import respx
from fastapi import HTTPException

from lib.providers.recommendation.listenbrainz import (
    ListenBrainzRecommendationProvider,
)
from tests.lib.providers.conftest import load_fixture


def _make_provider() -> ListenBrainzRecommendationProvider:
    return ListenBrainzRecommendationProvider()


class TestVerifyUsername:
    @respx.mock
    async def test_valid_user(self):
        username = "xdevolution"
        respx.get(f"https://api.listenbrainz.org/1/user/{username}/listen-count").mock(
            return_value=httpx.Response(
                200, json=load_fixture("listenbrainz/listen-count")
            )
        )
        provider = _make_provider()

        assert await provider.verify_username(username) is True

    @respx.mock
    async def test_invalid_user_404(self):
        username = "nobody"
        respx.get(f"https://api.listenbrainz.org/1/user/{username}/listen-count").mock(
            return_value=httpx.Response(404)
        )
        provider = _make_provider()

        assert await provider.verify_username(username) is False


class TestGetRecentTracks:
    @respx.mock
    async def test_returns_tracks(self):
        username = "xdevolution"
        respx.get(f"https://api.listenbrainz.org/1/user/{username}/listens").mock(
            return_value=httpx.Response(200, json=load_fixture("listenbrainz/listens"))
        )
        provider = _make_provider()
        result = await provider.get_recent_tracks(username=username, limit=10)

        assert len(result) > 0
        assert all(track.track_name for track in result)
        assert all(track.artist_name for track in result)
        assert all(track.album_name for track in result)
        assert all(track.duration for track in result)


class TestGetTopTracks:
    @respx.mock
    async def test_returns_tracks(self):
        respx.get(
            "https://api.listenbrainz.org/1/stats/user/xdevolution/recordings"
        ).mock(
            return_value=httpx.Response(
                200, json=load_fixture("listenbrainz/recordings")
            )
        )
        provider = _make_provider()
        result = await provider.get_top_tracks(
            username="xdevolution", period="7day", limit=10
        )

        assert len(result) > 0
        assert all(track.track_name for track in result)
        assert all(track.artist_name for track in result)
        assert all(track.musicbrainz_id for track in result)
        assert all(track.album_name for track in result)
        assert all(track.playcount for track in result)

    async def test_invalid_period(self):
        provider = _make_provider()

        with pytest.raises(HTTPException) as exc_info:
            await provider.get_top_tracks(username="alice", period="invalid")
        assert exc_info.value.status_code == 400


class TestGetSimilarTracks:
    @respx.mock
    async def test_returns_tracks(self):
        respx.get("https://api.listenbrainz.org/1/metadata/lookup/").mock(
            return_value=httpx.Response(
                200, json=load_fixture("listenbrainz/metadata-lookup")
            )
        )
        respx.get(
            "https://api.listenbrainz.org/1/lb-radio/artist/"
            "b9545342-1e6d-4dae-84ac-013374ad8d7c"
        ).mock(
            return_value=httpx.Response(
                200, json=load_fixture("listenbrainz/lb-radio-artist")
            )
        )
        respx.get("https://api.listenbrainz.org/1/metadata/recording/").mock(
            return_value=httpx.Response(
                200, json=load_fixture("listenbrainz/metadata-recording")
            )
        )

        provider = _make_provider()
        result = await provider.get_similar_tracks(
            artist_name="IU", track_name="Shopper", count=5
        )

        assert len(result) > 0
        assert all(track.track_name for track in result)
        assert all(track.artist_name for track in result)
        assert all(track.musicbrainz_id for track in result)
        assert all(track.year for track in result)
        assert all(track.duration for track in result)
