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


class TestGetArtistAlias:
    @respx.mock
    async def test_returns_name(self):
        respx.get("https://musicbrainz.org/ws/2/artist").mock(
            return_value=httpx.Response(200, json=load_fixture("musicbrainz/artist"))
        )

        provider = _make_provider()
        result = await provider.get_artist_alias(artist_name="Olivia Rodrigo")

        assert result == "Olivia Rodrigo"
