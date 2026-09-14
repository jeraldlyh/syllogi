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


class TestGetArtistAlbums:
    MBID = "b9545342-1e6d-4dae-84ac-013374ad8d7c"

    @respx.mock
    async def test_returns_albums(self):
        respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(
                200, json=load_fixture("lastfm/artist-getTopAlbums")
            )
        )

        provider = _make_provider()
        result = await provider.get_artist_albums(artist_mbid=self.MBID)

        assert len(result) == 50
        assert result[0].title == "IU 5th Album 'LILAC'"
        assert result[1].title == "Palette"
        assert result[1].id == "373e9186-e1a8-44fc-b16c-c7de57439a7e"
        assert (
            result[1].image_url
            == "https://lastfm-img.freetls.fastly.net/i/u/300x300/454afc10638676ca9b76882868be16bc.png"
        )
        assert all(album.title and album.image_url for album in result)

    @respx.mock
    async def test_missing_mbid_becomes_empty_id(self):
        respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(
                200, json=load_fixture("lastfm/artist-getTopAlbums")
            )
        )

        provider = _make_provider()
        result = await provider.get_artist_albums(artist_mbid=self.MBID)

        assert result[0].id == ""
        assert result[1].id == "373e9186-e1a8-44fc-b16c-c7de57439a7e"

    @respx.mock
    async def test_leaves_musicbrainz_only_fields_empty(self):
        respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(
                200, json=load_fixture("lastfm/artist-getTopAlbums")
            )
        )

        provider = _make_provider()
        result = await provider.get_artist_albums(artist_mbid=self.MBID)

        assert result[0].primary_type == ""
        assert result[0].secondary_types == []
        assert result[0].release_date == ""
        assert result[0].to_dict()["year"] == ""

    @respx.mock
    async def test_requests_top_albums_for_mbid(self):
        route = respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(
                200, json=load_fixture("lastfm/artist-getTopAlbums")
            )
        )

        provider = _make_provider()
        await provider.get_artist_albums(artist_mbid=self.MBID)

        params = route.calls.last.request.url.params

        assert params["method"] == "artist.getTopAlbums"
        assert params["mbid"] == self.MBID

    @respx.mock
    async def test_returns_empty_when_no_data(self):
        respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(204)
        )

        provider = _make_provider()
        result = await provider.get_artist_albums(artist_mbid=self.MBID)

        assert result == []

    @respx.mock
    async def test_returns_empty_when_no_albums(self):
        respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(200, json={})
        )

        provider = _make_provider()
        result = await provider.get_artist_albums(artist_mbid=self.MBID)

        assert result == []

    @respx.mock
    async def test_forwards_limit(self):
        route = respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(
                200, json=load_fixture("lastfm/artist-getTopAlbums")
            )
        )

        provider = _make_provider()
        result = await provider.get_artist_albums(artist_mbid=self.MBID, limit=10)

        params = route.calls.last.request.url.params

        assert params["limit"] == "10"
        assert params["method"] == "artist.getTopAlbums"
        assert params["mbid"] == self.MBID
        assert len(result) == 10

    @respx.mock
    async def test_handles_albums_without_images(self):
        payload = {
            "topalbums": {
                "album": [
                    {"name": "No Image Key", "mbid": "aaaa"},
                    {"name": "Null Image", "mbid": "bbbb", "image": None},
                    {"name": "Empty Image List", "mbid": "cccc", "image": []},
                ]
            }
        }
        respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(200, json=payload)
        )

        provider = _make_provider()
        result = await provider.get_artist_albums(artist_mbid=self.MBID)

        assert [album.title for album in result] == [
            "No Image Key",
            "Null Image",
            "Empty Image List",
        ]
        assert all(album.image_url == "" for album in result)


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


class TestSearchTracks:
    @respx.mock
    async def test_returns_multiple_tracks(self):
        respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(200, json=load_fixture("lastfm/track-search"))
        )

        provider = _make_provider()
        result = await provider.search_tracks(
            artist_name="IU", track_name="Celebrity", limit=10
        )

        assert len(result) == 10
        assert result[0].artist_name == "IU"
        assert result[0].track_name == "Celebrity"
        assert all(track.track_name for track in result)

    @respx.mock
    async def test_returns_empty_when_no_data(self):
        respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(204)
        )

        provider = _make_provider()
        result = await provider.search_tracks(artist_name="IU", track_name="Nobody")

        assert result == []

    async def test_returns_empty_when_no_criteria(self):
        provider = _make_provider()
        result = await provider.search_tracks()

        assert result == []

    @respx.mock
    async def test_ignores_album_name(self):
        route = respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(200, json=load_fixture("lastfm/track-search"))
        )

        provider = _make_provider()
        await provider.search_tracks(
            artist_name="IU", track_name="Celebrity", album_name="LILAC"
        )

        params = route.calls.last.request.url.params

        assert params["track"] == "Celebrity"
        assert params["artist"] == "IU"
        assert "album" not in params

    @respx.mock
    async def test_free_text_query_searched_as_track_term(self):
        route = respx.get("https://ws.audioscrobbler.com/2.0/").mock(
            return_value=httpx.Response(200, json=load_fixture("lastfm/track-search"))
        )

        provider = _make_provider()
        await provider.search_tracks(artist_name="IU", query="lilac iu")

        params = route.calls.last.request.url.params

        assert params["track"] == "lilac iu"
        assert params["artist"] == ""


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
