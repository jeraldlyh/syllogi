import httpx
import respx

from lib.providers.metadata.lastfm import LastFMMetadataProvider
from tests.lib.providers.conftest import load_fixture


def _make_provider() -> LastFMMetadataProvider:
    return LastFMMetadataProvider()


class TestGetNestedValue:
    def test_simple_path(self):
        provider = _make_provider()
        assert provider._get_nested_value({"a": 1}, "a") == 1

    def test_dotted_path(self):
        provider = _make_provider()
        assert provider._get_nested_value({"a": {"b": 2}}, "a.b") == 2

    def test_missing_key(self):
        provider = _make_provider()
        assert provider._get_nested_value({"a": 1}, "b") is None

    def test_non_dict_intermediate(self):
        provider = _make_provider()
        assert provider._get_nested_value({"a": "string"}, "a.b") is None


class TestGetArtistInfo:
    @respx.mock
    async def test_returns_artist(self):
        respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(200, json=load_fixture("lastfm/artist-getInfo"))
        )

        provider = _make_provider()
        result = await provider.get_artist_info(artist_name="IU")

        assert result is not None
        assert result.name == "IU"
        assert result.id == "b9545342-1e6d-4dae-84ac-013374ad8d7c"
        assert ["k-pop", "Korean", "female vocalists", "Kpop", "pop"] == result.tags


class TestGetArtistTrack:
    @respx.mock
    async def test_returns_matching_track(self):
        respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(200, json=load_fixture("lastfm/track-search"))
        )

        provider = _make_provider()
        result = await provider.get_artist_track(
            artist_name="IU", track_name="Celebrity"
        )

        assert result is not None
        assert result.artist_name == "IU"
        assert result.track_name == "Celebrity"


class TestGetAlbumInfo:
    @respx.mock
    async def test_returns_album(self):
        respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(200, json=load_fixture("lastfm/album-getInfo"))
        )

        provider = _make_provider()
        result = await provider.get_album_info(
            artist_name="IU", album_name="The Winning"
        )

        assert result is not None
        assert result.album_name == "The Winning"
        assert result.artist_name == "IU"
        assert (
            result.image_url
            == "https://lastfm.freetls.fastly.net/i/u/300x300/31f80134da715aec76a0a664080a01e7.jpg"
        )
        assert len(result.tracks) > 0
        for track in result.tracks:
            assert track.artist_name is not None
            assert track.track_name is not None
            assert track.duration_ms is not None
            assert track.album_name is not None


class TestGetChartTopTracks:
    @respx.mock
    async def test_returns_tracks(self):
        respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(
                200, json=load_fixture("lastfm/chart-getTopTracks")
            )
        )

        provider = _make_provider()
        result = await provider.get_chart_top_tracks(limit=5)

        assert len(result) > 0

        for track in result:
            assert track.artist_name is not None
            assert track.track_name is not None
            assert track.duration is not None
            assert track.listeners is not None
            assert track.playcount is not None
            assert track.musicbrainz_id is not None
