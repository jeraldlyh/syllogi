import httpx
import respx

from lib.providers.metadata.musicbrainz import MusicBrainzMetadataProvider
from tests.lib.providers.conftest import load_fixture


def _make_provider() -> MusicBrainzMetadataProvider:
    return MusicBrainzMetadataProvider()


class TestGetArtistInfo:
    @respx.mock
    async def test_returns_artist(self):
        respx.get("https://musicbrainz.org/ws/2/artist").mock(
            return_value=httpx.Response(200, json=load_fixture("musicbrainz/artist"))
        )

        provider = _make_provider()
        result = await provider.get_artist_info(artist_name="Test Artist")

        assert result is not None
        assert result.name == "Olivia Rodrigo"
        assert result.area == "United States"
        assert result.begin_area == "Murrieta"


class TestGetArtistTrack:
    @respx.mock
    async def test_returns_track(self):
        respx.get("https://musicbrainz.org/ws/2/recording").mock(
            return_value=httpx.Response(200, json=load_fixture("musicbrainz/recording"))
        )

        provider = _make_provider()
        result = await provider.get_artist_track(artist_name="IU", track_name="Track")

        assert result is not None
        assert result.artist_name == "IU"
        assert result.track_name == "Celebrity"
        assert result.duration_ms == 195000
        assert result.album_name == "LILAC"


class TestSearchTracks:
    @respx.mock
    async def test_returns_tracks_matching_artist_and_track(self):
        respx.get("https://musicbrainz.org/ws/2/recording").mock(
            return_value=httpx.Response(200, json=load_fixture("musicbrainz/recording"))
        )

        provider = _make_provider()
        result = await provider.search_tracks(artist_name="IU", track_name="Celebrity")

        assert len(result) == 1
        assert result[0].artist_name == "IU"
        assert result[0].track_name == "Celebrity"
        assert result[0].duration_ms == 195000
        assert result[0].album_name == "LILAC"

    @respx.mock
    async def test_returns_tracks_by_track_name_only(self):
        respx.get("https://musicbrainz.org/ws/2/recording").mock(
            return_value=httpx.Response(200, json=load_fixture("musicbrainz/recording"))
        )

        provider = _make_provider()
        result = await provider.search_tracks(artist_name="", track_name="Celebrity")

        assert len(result) == 1
        assert result[0].artist_name == "IU"

    async def test_returns_empty_when_no_query(self):
        provider = _make_provider()
        result = await provider.search_tracks(artist_name="", track_name="")

        assert result == []

    @respx.mock
    async def test_returns_empty_when_no_matches(self):
        respx.get("https://musicbrainz.org/ws/2/recording").mock(
            return_value=httpx.Response(200, json={"recordings": []})
        )

        provider = _make_provider()
        result = await provider.search_tracks(artist_name="", track_name="Nobody")

        assert result == []

    @respx.mock
    async def test_populates_recording_fields(self):
        route = respx.get("https://musicbrainz.org/ws/2/recording").mock(
            return_value=httpx.Response(200, json=load_fixture("musicbrainz/recording"))
        )

        provider = _make_provider()
        result = await provider.search_tracks(artist_name="IU", track_name="Celebrity")

        assert result[0].id
        assert result[0].get_year() == result[0].release_date.split("-")[0]
        assert route.called

    @respx.mock
    async def test_builds_release_clause_from_album_name(self):
        route = respx.get("https://musicbrainz.org/ws/2/recording").mock(
            return_value=httpx.Response(200, json=load_fixture("musicbrainz/recording"))
        )

        provider = _make_provider()
        await provider.search_tracks(
            artist_name="IU", track_name="Celebrity", album_name="LILAC"
        )

        sent = route.calls.last.request.url.params["query"]

        assert 'recording:"Celebrity"' in sent
        assert 'artist:"IU"' in sent
        assert 'release:"LILAC"' in sent

    @respx.mock
    async def test_free_text_query_replaces_field_clauses(self):
        route = respx.get("https://musicbrainz.org/ws/2/recording").mock(
            return_value=httpx.Response(200, json=load_fixture("musicbrainz/recording"))
        )

        provider = _make_provider()
        await provider.search_tracks(
            artist_name="IU", track_name="Celebrity", query="lilac iu"
        )

        assert route.calls.last.request.url.params["query"] == "lilac iu"

    @respx.mock
    async def test_escapes_lucene_operators_in_field_clauses(self):
        route = respx.get("https://musicbrainz.org/ws/2/recording").mock(
            return_value=httpx.Response(200, json=load_fixture("musicbrainz/recording"))
        )

        provider = _make_provider()
        await provider.search_tracks(
            artist_name="AC/DC", track_name='10" Vinyl (Remix)'
        )

        sent = route.calls.last.request.url.params["query"]

        assert 'recording:"10\\" Vinyl \\(Remix\\)"' in sent
        assert 'artist:"AC\\/DC"' in sent

    @respx.mock
    async def test_leaves_the_free_text_query_unescaped(self):
        route = respx.get("https://musicbrainz.org/ws/2/recording").mock(
            return_value=httpx.Response(200, json=load_fixture("musicbrainz/recording"))
        )

        provider = _make_provider()
        await provider.search_tracks(query='recording:"Celebrity" AND artist:"IU"')

        sent = route.calls.last.request.url.params["query"]

        assert sent == 'recording:"Celebrity" AND artist:"IU"'


class TestGetAlbumInfo:
    @respx.mock
    async def test_returns_album(self):
        respx.get("https://musicbrainz.org/ws/2/release-group").mock(
            return_value=httpx.Response(
                200, json=load_fixture("musicbrainz/release-group")
            )
        )
        respx.get(
            "https://musicbrainz.org/ws/2/release/d1560bef-8a26-46c0-8102-f5fd5edb0fd2"
        ).mock(
            return_value=httpx.Response(200, json=load_fixture("musicbrainz/release"))
        )

        provider = _make_provider()
        result = await provider.get_album_info(
            artist_name="KARIHAXAT", album_name="Create a new release group"
        )

        assert result is not None
        assert result.artist_name == "KARIHAXAT"
        assert result.album_name == "Create a new release group"
        assert result.release_date == "2025-05-24"
        assert len(result.tracks) > 0
        for track in result.tracks:
            assert track.artist_name is not None
            assert track.track_name is not None
            assert track.duration_ms is not None
            assert track.disambiguation is not None
            assert track.album_name is not None


class TestSearchArtists:
    @respx.mock
    async def test_returns_multiple_artists(self):
        respx.get("https://musicbrainz.org/ws/2/artist").mock(
            return_value=httpx.Response(200, json=load_fixture("musicbrainz/artist"))
        )

        provider = _make_provider()
        result = await provider.search_artists(query="Olivia", limit=10)

        assert len(result) == 10
        assert result[0].name == "Olivia Rodrigo"
        assert all(artist.name for artist in result)

    @respx.mock
    async def test_returns_empty_when_no_matches(self):
        respx.get("https://musicbrainz.org/ws/2/artist").mock(
            return_value=httpx.Response(200, json={"artists": []})
        )

        provider = _make_provider()
        result = await provider.search_artists(query="Nobody")

        assert result == []


class TestGetArtistAlias:
    @respx.mock
    async def test_returns_name(self):
        respx.get("https://musicbrainz.org/ws/2/artist").mock(
            return_value=httpx.Response(200, json=load_fixture("musicbrainz/artist"))
        )

        provider = _make_provider()
        result = await provider.get_artist_alias(artist_name="Olivia Rodrigo")

        assert result == "Olivia Rodrigo"
