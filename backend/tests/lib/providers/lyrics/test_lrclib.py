import httpx
import pytest
import respx

from lib.models.library import LyricsCandidate
from lib.providers.lyrics.lrclib import LRCLIBLyricsProvider
from tests.lib.providers.conftest import load_fixture


def _make_provider() -> LRCLIBLyricsProvider:
    return LRCLIBLyricsProvider()


def make_candidate(**overrides) -> LyricsCandidate:
    fields = {
        "id": 1,
        "track_name": "I Want to Live",
        "artist_name": "Borislav Slavov",
        "album_name": "Baldur's Gate 3 (Original Game Soundtrack)",
        "duration": 233,
        "instrumental": False,
        "plain_lyrics": "I feel your breath upon my neck",
        "synced_lyrics": "[00:17.12] I feel your breath upon my neck",
    }
    fields.update(overrides)

    return LyricsCandidate(**fields)


class TestSearchLyrics:
    @respx.mock
    async def test_returns_every_candidate(self):
        respx.get("https://lrclib.net/api/search").mock(
            return_value=httpx.Response(200, json=load_fixture("lrclib_search"))
        )

        results = await _make_provider().search_lyrics(
            artist_name="Borislav Slavov",
            track_name="I Want to Live",
            album_name="Baldur's Gate 3 (Original Game Soundtrack)",
        )

        assert len(results) == 4
        assert results[0].instrumental is True
        assert "[00:17.12]" in results[-1].synced_lyrics

    @respx.mock
    async def test_searches_by_track_when_no_query_is_given(self):
        route = respx.get("https://lrclib.net/api/search").mock(
            return_value=httpx.Response(200, json=[])
        )

        await _make_provider().search_lyrics(
            artist_name="Borislav Slavov",
            track_name="I Want to Live",
            album_name="Album",
        )

        params = route.calls.last.request.url.params
        assert params["track_name"] == "I Want to Live"
        assert params["artist_name"] == "Borislav Slavov"
        assert params["album_name"] == "Album"
        assert "q" not in params

    @respx.mock
    async def test_a_free_text_query_replaces_the_fields(self):
        route = respx.get("https://lrclib.net/api/search").mock(
            return_value=httpx.Response(200, json=[])
        )

        await _make_provider().search_lyrics(
            query="borislav slavov i want to live",
            track_name="ignored",
        )

        params = route.calls.last.request.url.params
        assert params["q"] == "borislav slavov i want to live"
        assert "track_name" not in params

    async def test_returns_nothing_without_a_track_or_query(self):
        assert await _make_provider().search_lyrics() == []

    @respx.mock
    async def test_honours_the_limit(self):
        respx.get("https://lrclib.net/api/search").mock(
            return_value=httpx.Response(200, json=load_fixture("lrclib_search"))
        )

        results = await _make_provider().search_lyrics(
            track_name="I Want to Live", limit=2
        )

        assert len(results) == 2

    @respx.mock
    async def test_returns_nothing_on_404(self):
        respx.get("https://lrclib.net/api/search").mock(
            return_value=httpx.Response(404)
        )

        assert await _make_provider().search_lyrics(track_name="Track") == []

    @respx.mock
    async def test_returns_nothing_on_http_error(self):
        respx.get("https://lrclib.net/api/search").mock(
            return_value=httpx.Response(500)
        )

        assert await _make_provider().search_lyrics(track_name="Track") == []


class TestSelectLyrics:
    def test_prefers_synced_lyrics(self):
        candidates = [
            make_candidate(id=1, synced_lyrics=""),
            make_candidate(id=2),
        ]

        assert (
            LRCLIBLyricsProvider()
            .select_lyrics(candidates=candidates, duration=233)
            .startswith("[00:17.12]")
        )

    def test_falls_back_to_plain_lyrics(self):
        candidates = [make_candidate(synced_lyrics="")]

        assert LRCLIBLyricsProvider().select_lyrics(
            candidates=candidates, duration=233
        ) == ("I feel your breath upon my neck")

    def test_skips_instrumental_candidates(self):
        candidates = [
            make_candidate(instrumental=True, plain_lyrics="", synced_lyrics=""),
            make_candidate(id=2),
        ]

        assert (
            LRCLIBLyricsProvider()
            .select_lyrics(candidates=candidates, duration=233)
            .startswith("[00:17.12]")
        )

    def test_skips_candidates_recorded_at_a_different_length(self):
        candidates = [make_candidate(duration=400)]

        assert (
            LRCLIBLyricsProvider().select_lyrics(candidates=candidates, duration=233)
            == ""
        )

    @pytest.mark.parametrize("duration", [231, 233, 235])
    def test_accepts_a_two_second_difference(self, duration):
        candidates = [make_candidate(duration=233)]

        assert (
            LRCLIBLyricsProvider().select_lyrics(
                candidates=candidates, duration=duration
            )
            != ""
        )

    def test_ignores_duration_when_the_track_length_is_unknown(self):
        candidates = [make_candidate(duration=400)]

        assert (
            LRCLIBLyricsProvider().select_lyrics(candidates=candidates, duration=0)
            != ""
        )

    def test_returns_nothing_without_candidates(self):
        assert LRCLIBLyricsProvider().select_lyrics(candidates=[], duration=233) == ""

    def test_returns_nothing_when_every_candidate_is_empty(self):
        candidates = [make_candidate(plain_lyrics="", synced_lyrics="")]

        assert (
            LRCLIBLyricsProvider().select_lyrics(candidates=candidates, duration=233)
            == ""
        )
