import httpx
import pytest
import respx
from fastapi import HTTPException

from lib.providers.recommendation.lastfm import (
    LastFMRecommendationProvider,
    _extract_year,
)
from tests.lib.providers.conftest import load_fixture


def _make_provider() -> LastFMRecommendationProvider:
    return LastFMRecommendationProvider()


class TestExtractYear:
    def test_extracts_year(self):
        assert _extract_year({"date": {"uts": "1700000000"}}) == "2023"

    def test_empty_uts(self):
        assert _extract_year({"date": {}}) == ""

    def test_missing_date(self):
        assert _extract_year({}) == ""

    def test_invalid_uts(self):
        assert _extract_year({"date": {"uts": "invalid"}}) == ""


class TestGetNestedValue:
    def test_simple(self):
        provider = _make_provider()
        assert provider._get_nested_value({"a": 1}, "a") == 1

    def test_dotted(self):
        provider = _make_provider()
        assert provider._get_nested_value({"a": {"b": 2}}, "a.b") == 2

    def test_missing(self):
        provider = _make_provider()
        assert provider._get_nested_value({}, "a.b") is None


class TestVerifyUsername:
    @respx.mock
    async def test_valid_user(self):
        respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(200, json=load_fixture("lastfm/user-getInfo"))
        )
        provider = _make_provider()

        assert await provider.verify_username("alice") is True


class TestGetTopTracks:
    @respx.mock
    async def test_returns_tracks(self):
        respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(
                200, json=load_fixture("lastfm/user-getTopTracks")
            )
        )
        provider = _make_provider()
        result = await provider.get_top_tracks(
            username="alice", period="6month", limit=5
        )

        assert len(result) > 0
        assert all(track.artist_name for track in result)
        assert all(track.track_name for track in result)
        assert all(track.duration for track in result)
        assert all(track.musicbrainz_id for track in result)
        assert all(track.playcount for track in result)

    async def test_invalid_period(self):
        provider = _make_provider()

        with pytest.raises(HTTPException) as exc_info:
            await provider.get_top_tracks(username="alice", period="invalid")
        assert exc_info.value.status_code == 400


class TestGetSimilarTracks:
    @respx.mock
    async def test_returns_tracks(self):
        respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(
                200, json=load_fixture("lastfm/user-getSimilarTracks")
            )
        )
        provider = _make_provider()
        result = await provider.get_similar_tracks(
            artist_name="Artist", track_name="Track", count=5
        )

        assert len(result) == 5
        assert all(track.artist_name for track in result)
        assert all(track.track_name for track in result)
        assert all(track.duration for track in result)
        assert all(track.musicbrainz_id for track in result)
        assert all(track.playcount for track in result)
        assert all(track.similarity_score for track in result)
