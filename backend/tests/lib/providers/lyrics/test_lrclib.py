import httpx
import respx

from lib.providers.lyrics.lrclib import LRCLIBLyricsProvider
from tests.lib.providers.conftest import load_fixture


def _make_provider() -> LRCLIBLyricsProvider:
    return LRCLIBLyricsProvider()


class TestGetLyrics:
    @respx.mock
    async def test_returns_synced_lyrics(self):
        respx.get("https://lrclib.net/api/get").mock(
            return_value=httpx.Response(200, json=load_fixture("lrclib"))
        )

        provider = _make_provider()
        result = await provider.get_lyrics(
            artist_name="Borislav Slavov",
            track_name="I Want to Live",
            album_name="Baldur's Gate 3 (Original Game Soundtrack)",
            duration=233,
        )

        assert result is not None
        assert "[00:17.12]" in result
        assert "[03:20.31]" in result
        assert result == result.strip()

    @respx.mock
    async def test_returns_none_on_404(self):
        respx.get("https://lrclib.net/api/get").mock(return_value=httpx.Response(404))

        provider = _make_provider()
        result = await provider.get_lyrics(
            artist_name="Artist",
            track_name="Track",
            album_name="Album",
            duration=200,
        )

        assert result is None

    @respx.mock
    async def test_returns_none_on_http_error(self):
        respx.get("https://lrclib.net/api/get").mock(return_value=httpx.Response(500))

        provider = _make_provider()
        result = await provider.get_lyrics(
            artist_name="Artist",
            track_name="Track",
            album_name="Album",
            duration=200,
        )

        assert result is None
