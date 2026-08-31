import httpx
import pytest
import respx

from lib.providers.metadata.deezer import DeezerMetadataProvider
from tests.lib.providers.conftest import load_fixture


def _make_provider() -> DeezerMetadataProvider:
    return DeezerMetadataProvider()


class TestGetArtistInfo:
    @respx.mock
    async def test_returns_artist_info(self):
        respx.get("https://api.deezer.com/search/artist").mock(
            return_value=httpx.Response(200, json=load_fixture("deezer/search-artist"))
        )

        provider = _make_provider()
        result = await provider.get_artist_info(artist_name="IU")

        assert result is not None
        assert result.id == "2810121"
        assert result.name == "IU"
        assert (
            result.image_url
            == "https://cdn-images.dzcdn.net/images/artist/c619e4cef93d6fa98a38018d92106bb6/500x500-000000-80-0-0.jpg"
        )
        assert result.num_of_fans == 305331

    @respx.mock
    async def test_returns_none_on_error(self):
        respx.get("https://api.deezer.com/search/artist").mock(
            return_value=httpx.Response(500)
        )

        provider = _make_provider()
        result = await provider.get_artist_info(artist_name="Nobody")

        assert result is None


class TestGetArtistTrack:
    @respx.mock
    async def test_returns_track(self):
        respx.get("https://api.deezer.com/search/track").mock(
            return_value=httpx.Response(200, json=load_fixture("deezer/search-track"))
        )

        provider = _make_provider()
        result = await provider.get_artist_track(
            artist_name="IU", track_name="Celebrity"
        )

        assert result is not None
        assert result.artist_name == "IU"
        assert result.track_name == "Celebrity"
        assert result.album_name == "Celebrity"
        assert result.duration_ms == 195000
        assert (
            result.image_url
            == "https://cdn-images.dzcdn.net/images/cover/9fcc61fee5df1b9e845a618feaa70b72/500x500-000000-80-0-0.jpg"
        )


class TestSearchTracks:
    @respx.mock
    async def test_returns_multiple_tracks(self):
        respx.get("https://api.deezer.com/search/track").mock(
            return_value=httpx.Response(200, json=load_fixture("deezer/search-track"))
        )

        provider = _make_provider()
        result = await provider.search_tracks(
            artist_name="", track_name="Celebrity", limit=10
        )

        assert len(result) == 5
        assert result[0].artist_name == "IU"
        assert result[0].track_name == "Celebrity"
        assert result[0].album_name == "Celebrity"
        assert result[0].duration_ms == 195000
        assert all(track.track_name for track in result)

    @respx.mock
    async def test_returns_empty_on_error(self):
        respx.get("https://api.deezer.com/search/track").mock(
            return_value=httpx.Response(500)
        )

        provider = _make_provider()
        result = await provider.search_tracks(artist_name="", track_name="Nobody")

        assert result == []

    async def test_returns_empty_when_no_criteria(self):
        provider = _make_provider()
        result = await provider.search_tracks()

        assert result == []

    @respx.mock
    async def test_folds_album_name_into_query(self):
        route = respx.get("https://api.deezer.com/search/track").mock(
            return_value=httpx.Response(200, json=load_fixture("deezer/search-track"))
        )

        provider = _make_provider()
        await provider.search_tracks(
            artist_name="IU", track_name="Celebrity", album_name="LILAC"
        )

        assert route.calls.last.request.url.params["q"] == "IU Celebrity LILAC"

    @respx.mock
    async def test_free_text_query_replaces_field_terms(self):
        route = respx.get("https://api.deezer.com/search/track").mock(
            return_value=httpx.Response(200, json=load_fixture("deezer/search-track"))
        )

        provider = _make_provider()
        await provider.search_tracks(artist_name="IU", query="lilac iu")

        assert route.calls.last.request.url.params["q"] == "lilac iu"


class TestGetAlbumInfo:
    @respx.mock
    async def test_returns_album_with_tracks(self):
        respx.get("https://api.deezer.com/search/album").mock(
            return_value=httpx.Response(200, json=load_fixture("deezer/search-album"))
        )
        respx.get("https://api.deezer.com/album/203090382/tracks").mock(
            return_value=httpx.Response(200, json=load_fixture("deezer/album-tracks"))
        )

        provider = _make_provider()
        result = await provider.get_album_info(artist_name="Artist", album_name="Album")

        assert result is not None
        assert result.album_name == "Celebrity"
        assert result.artist_name == "IU"
        assert (
            result.image_url
            == "https://cdn-images.dzcdn.net/images/cover/9fcc61fee5df1b9e845a618feaa70b72/1000x1000-000000-80-0-0.jpg"
        )
        assert all(track.track_name for track in result.tracks)
        assert len(result.tracks) == 1


class TestGetChartTopTracks:
    @respx.mock
    async def test_returns_tracks(self):
        respx.get("https://api.deezer.com/chart/0/tracks").mock(
            return_value=httpx.Response(200, json=load_fixture("deezer/chart-tracks"))
        )

        provider = _make_provider()
        result = await provider.get_chart_top_tracks(limit=1)

        assert len(result) > 0
        assert all(track.artist_name for track in result)
        assert all(track.track_name for track in result)
        assert all(track.album_name for track in result)
        assert all(track.duration for track in result)
        assert all(track.image_url for track in result)

    @respx.mock
    async def test_returns_empty_on_error(self):
        respx.get("https://api.deezer.com/chart/0/tracks").mock(
            return_value=httpx.Response(500)
        )

        provider = _make_provider()
        result = await provider.get_chart_top_tracks()

        assert result == []


class TestGetArtistTracks:
    async def test_raises_not_implemented(self):
        provider = _make_provider()

        with pytest.raises(NotImplementedError):
            await provider.get_artist_tracks(artist_mbid="123")
