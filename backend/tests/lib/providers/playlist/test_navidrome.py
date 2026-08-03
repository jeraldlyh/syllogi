import asyncio
import json
from unittest.mock import AsyncMock

import httpx
import pytest
import respx

from lib.models.provider import ProviderError
from lib.providers.playlist.navidrome import NavidromeProvider
from tests.lib.providers.conftest import load_fixture

_NAVIDROME_URL = "https://navidrome.example.com"


def _make_provider() -> NavidromeProvider:
    return NavidromeProvider()


def _subsonic_ok() -> dict:
    return {"subsonic-response": {"status": "ok", "version": "1.16.1"}}


class TestSubsonic:
    @respx.mock
    async def test_returns_parsed_subsonic_data(self):
        route = respx.get(f"{_NAVIDROME_URL}/rest/getPlaylists")
        route.mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/playlists"))
        )

        provider = _make_provider()
        data = await provider._subsonic(
            "getPlaylists", username="admin", password="adminpass"
        )

        assert "status" not in data
        assert "version" not in data

        params = route.calls[0].request.url.params
        assert params.get("u") == "admin"
        assert params.get("v") == "1.16.1"
        assert params.get("c") == "syllogi"
        assert params.get("f") == "json"
        assert params.get("t")
        assert params.get("s")

    @respx.mock
    async def test_returns_empty_dict_on_non_ok_status(self):
        respx.get(f"{_NAVIDROME_URL}/rest/getPlaylists").mock(
            return_value=httpx.Response(
                200,
                json={
                    "subsonic-response": {
                        "status": "failed",
                        "version": "1.16.1",
                        "type": "navidrome",
                        "serverVersion": "0.62.0 (1b46b977)",
                        "openSubsonic": True,
                        "error": {"code": 40, "message": "Wrong username or password"},
                    }
                },
            )
        )

        provider = _make_provider()
        data = await provider._subsonic(
            "getPlaylists", username="admin", password="adminpass"
        )

        assert data == {}

    @respx.mock
    async def test_raises_on_http_error(self):
        respx.get(f"{_NAVIDROME_URL}/rest/getPlaylists").mock(
            return_value=httpx.Response(500)
        )

        provider = _make_provider()
        with pytest.raises(httpx.HTTPStatusError):
            await provider._subsonic(
                "getPlaylists", username="admin", password="adminpass"
            )


class TestGetBearerToken:
    @respx.mock
    async def test_returns_token_and_caches(self):
        login_route = respx.post(f"{_NAVIDROME_URL}/auth/login")
        login_route.mock(
            return_value=httpx.Response(200, json={"token": "jwt-token-123"})
        )

        provider = _make_provider()
        token = await provider._get_bearer_token()
        token_cached = await provider._get_bearer_token()

        assert token == "jwt-token-123"
        assert token_cached == "jwt-token-123"
        assert login_route.call_count == 1
        assert json.loads(login_route.calls[0].request.content) == {
            "username": "admin",
            "password": "adminpass",
        }

    @respx.mock
    async def test_returns_none_when_token_missing(self):
        respx.post(f"{_NAVIDROME_URL}/auth/login").mock(
            return_value=httpx.Response(
                200, json={"error": "Invalid username or password"}
            )
        )

        provider = _make_provider()
        token = await provider._get_bearer_token()

        assert token is None

    @respx.mock
    async def test_returns_none_on_http_error(self):
        respx.post(f"{_NAVIDROME_URL}/auth/login").mock(
            return_value=httpx.Response(500)
        )

        provider = _make_provider()
        token = await provider._get_bearer_token()

        assert token is None


class TestApi:
    @respx.mock
    async def test_returns_json_on_success(self):
        token = "token-1"
        respx.post(f"{_NAVIDROME_URL}/auth/login").mock(
            return_value=httpx.Response(200, json={"token": token})
        )
        user_route = respx.get(f"{_NAVIDROME_URL}/api/user")
        user_route.mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/users"))
        )

        provider = _make_provider()
        result = await provider._api("api/user")

        assert result == load_fixture("navidrome/users")
        assert user_route.call_count == 1
        assert (
            user_route.calls[0].request.headers["X-ND-Authorization"]
            == f"Bearer {token}"
        )

    @respx.mock
    async def test_refreshes_token_and_retries_on_401(self):
        login_route = respx.post(f"{_NAVIDROME_URL}/auth/login")
        login_route.mock(
            side_effect=[
                httpx.Response(200, json={"token": "token-1"}),
                httpx.Response(200, json={"token": "token-2"}),
            ]
        )
        user_route = respx.get(f"{_NAVIDROME_URL}/api/user")
        user_route.mock(
            side_effect=[
                httpx.Response(401, json={"error": "unauthorized"}),
                httpx.Response(200, json=load_fixture("navidrome/users")),
            ]
        )

        provider = _make_provider()
        result = await provider._api("api/user")

        assert result == load_fixture("navidrome/users")
        assert login_route.call_count == 2
        assert user_route.call_count == 2

    @respx.mock
    async def test_returns_empty_dict_on_non_401_http_error(self):
        respx.post(f"{_NAVIDROME_URL}/auth/login").mock(
            return_value=httpx.Response(200, json={"token": "token-1"})
        )
        respx.get(f"{_NAVIDROME_URL}/api/user").mock(return_value=httpx.Response(500))

        provider = _make_provider()
        result = await provider._api("api/user")

        assert result == {}

    @respx.mock
    async def test_returns_empty_dict_when_no_token(self):
        respx.post(f"{_NAVIDROME_URL}/auth/login").mock(
            return_value=httpx.Response(200, json={})
        )
        user_route = respx.get(f"{_NAVIDROME_URL}/api/user")
        user_route.mock(return_value=httpx.Response(200, json=[]))

        provider = _make_provider()
        result = await provider._api("api/user")

        assert result == {}
        assert user_route.call_count == 0


class TestGetUsers:
    @respx.mock
    async def test_returns_users_single_page(self):
        respx.post(f"{_NAVIDROME_URL}/auth/login").mock(
            return_value=httpx.Response(200, json={"token": "token-1"})
        )
        user_route = respx.get(f"{_NAVIDROME_URL}/api/user")
        user_route.mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/users"))
        )

        provider = _make_provider()
        users = await provider.get_users()

        assert len(users) == 2
        assert users[0].id == "user-1"
        assert users[0].name == "apple"
        assert users[1].id == "user-2"
        assert users[1].name == "berry"

        params = user_route.calls[0].request.url.params
        assert params.get("_start") == "0"
        assert params.get("_end") == "100"
        assert params.get("_sort") == "userName"
        assert params.get("_order") == "ASC"

    @respx.mock
    async def test_returns_empty_when_first_page_empty(self):
        respx.post(f"{_NAVIDROME_URL}/auth/login").mock(
            return_value=httpx.Response(200, json={"token": "token-1"})
        )
        user_route = respx.get(f"{_NAVIDROME_URL}/api/user")
        user_route.mock(return_value=httpx.Response(200, json=[]))

        provider = _make_provider()
        users = await provider.get_users()

        assert users == []
        assert user_route.call_count == 1


class TestGetUserByName:
    @respx.mock
    async def test_returns_matching_user(self):
        respx.post(f"{_NAVIDROME_URL}/auth/login").mock(
            return_value=httpx.Response(200, json={"token": "token-1"})
        )
        respx.get(f"{_NAVIDROME_URL}/api/user").mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/users"))
        )

        provider = _make_provider()
        user = await provider.get_user_by_name("apple")

        assert user is not None
        assert user.id == "user-1"
        assert user.name == "apple"

    @respx.mock
    async def test_returns_none_when_not_found(self):
        respx.post(f"{_NAVIDROME_URL}/auth/login").mock(
            return_value=httpx.Response(200, json={"token": "token-1"})
        )
        respx.get(f"{_NAVIDROME_URL}/api/user").mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/users"))
        )

        provider = _make_provider()
        user = await provider.get_user_by_name("missing-user")

        assert user is None


class TestGetPlaylists:
    @respx.mock
    async def test_returns_playlists(self):
        route = respx.get(f"{_NAVIDROME_URL}/rest/getPlaylists")
        route.mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/playlists"))
        )

        provider = _make_provider()
        playlists = await provider.get_playlists(
            user_id="user-1", username="admin", password="adminpass"
        )

        assert len(playlists) == 2
        assert playlists[0].id == "playlist-1"
        assert playlists[0].name == "Daily Recommendations"
        assert playlists[1].id == "playlist-2"
        assert playlists[1].name == "The Daily Ketchup Podcast"

    @respx.mock
    async def test_wraps_single_dict_playlist(self):
        mocked_response = load_fixture("navidrome/playlists")
        mocked_response["subsonic-response"]["playlists"]["playlist"] = mocked_response[
            "subsonic-response"
        ]["playlists"]["playlist"][0]

        respx.get(f"{_NAVIDROME_URL}/rest/getPlaylists").mock(
            return_value=httpx.Response(
                200,
                json=mocked_response,
            )
        )

        provider = _make_provider()
        playlists = await provider.get_playlists(
            user_id="user-1", username="admin", password="adminpass"
        )

        assert len(playlists) == 1
        assert playlists[0].id == "playlist-1"
        assert playlists[0].name == "Daily Recommendations"

    @respx.mock
    async def test_returns_empty_when_no_playlists(self):
        respx.get(f"{_NAVIDROME_URL}/rest/getPlaylists").mock(
            return_value=httpx.Response(200, json=_subsonic_ok())
        )

        provider = _make_provider()
        playlists = await provider.get_playlists(
            user_id="user-1", username="admin", password="adminpass"
        )

        assert playlists == []


class TestGetOrCreatePlaylist:
    @respx.mock
    async def test_returns_existing_playlist(self):
        respx.post(f"{_NAVIDROME_URL}/auth/login").mock(
            return_value=httpx.Response(200, json={"token": "token-1"})
        )
        respx.get(f"{_NAVIDROME_URL}/api/user").mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/users"))
        )
        respx.get(f"{_NAVIDROME_URL}/rest/getPlaylists").mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/playlists"))
        )
        update_route = respx.post(f"{_NAVIDROME_URL}/rest/updatePlaylist")
        update_route.mock(return_value=httpx.Response(200, json=_subsonic_ok()))

        provider = _make_provider()
        playlist_id, user_id = await provider.get_or_create_playlist(
            playlist_name="Daily Recommendations",
            username="apple",
            password="adminpass",
        )

        assert playlist_id == "playlist-1"
        assert user_id == "user-1"
        assert update_route.call_count == 1
        assert (
            update_route.calls[0].request.url.params.get("playlistId") == "playlist-1"
        )
        assert update_route.calls[0].request.url.params.get("public") == "false"

    @respx.mock
    async def test_creates_new_playlist_when_missing(self):
        respx.post(f"{_NAVIDROME_URL}/auth/login").mock(
            return_value=httpx.Response(200, json={"token": "token-1"})
        )
        respx.get(f"{_NAVIDROME_URL}/api/user").mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/users"))
        )
        get_playlists_route = respx.get(f"{_NAVIDROME_URL}/rest/getPlaylists")
        get_playlists_route.mock(
            side_effect=[
                httpx.Response(200, json=_subsonic_ok()),
                httpx.Response(
                    200,
                    json=load_fixture("navidrome/playlists"),
                ),
            ]
        )
        create_route = respx.post(f"{_NAVIDROME_URL}/rest/createPlaylist")
        create_route.mock(
            return_value=httpx.Response(
                200, json=load_fixture("navidrome/create-playlist")
            )
        )
        update_route = respx.post(f"{_NAVIDROME_URL}/rest/updatePlaylist")
        update_route.mock(return_value=httpx.Response(200, json=_subsonic_ok()))

        provider = _make_provider()
        playlist_id, user_id = await provider.get_or_create_playlist(
            playlist_name="Daily Recommendations",
            username="apple",
            password="adminpass",
        )

        assert playlist_id == "playlist-1"
        assert user_id == "user-1"
        assert create_route.call_count == 1
        assert update_route.call_count == 1
        assert (
            update_route.calls[0].request.url.params.get("playlistId") == "playlist-1"
        )
        assert update_route.calls[0].request.url.params.get("public") == "false"

    @respx.mock
    async def test_raises_when_user_not_found(self):
        respx.post(f"{_NAVIDROME_URL}/auth/login").mock(
            return_value=httpx.Response(200, json={"token": "token-1"})
        )
        respx.get(f"{_NAVIDROME_URL}/api/user").mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/users"))
        )

        provider = _make_provider()
        with pytest.raises(ProviderError, match="Unable to find username"):
            await provider.get_or_create_playlist(
                playlist_name="Favorites", username="missing-user", password="adminpass"
            )


class TestCreatePlaylist:
    @respx.mock
    async def test_creates_playlist(self):
        route = respx.post(f"{_NAVIDROME_URL}/rest/createPlaylist")
        route.mock(
            return_value=httpx.Response(
                200, json=load_fixture("navidrome/create-playlist")
            )
        )

        provider = _make_provider()
        playlist = await provider.create_playlist(
            playlist_name="Favourites",
            user_id="user-1",
            username="apple",
            password="adminpass",
        )

        assert playlist.id == "playlist-1"
        assert playlist.name == "Favourites"
        assert route.calls[0].request.url.params.get("name") == "Favourites"

    @respx.mock
    async def test_raises_on_http_error(self):
        respx.post(f"{_NAVIDROME_URL}/rest/createPlaylist").mock(
            return_value=httpx.Response(500)
        )

        provider = _make_provider()
        with pytest.raises(httpx.HTTPStatusError):
            await provider.create_playlist(
                playlist_name="New Playlist",
                user_id="1",
                username="admin",
                password="adminpass",
            )


class TestDeletePlaylist:
    @respx.mock
    async def test_deletes_playlist(self):
        route = respx.post(f"{_NAVIDROME_URL}/rest/deletePlaylist")
        route.mock(return_value=httpx.Response(200, json=_subsonic_ok()))

        provider = _make_provider()
        result = await provider.delete_playlist(
            playlist_id="playlist-1", username="admin", password="adminpass"
        )

        assert result is None
        assert route.calls[0].request.url.params.get("id") == "playlist-1"


class TestGetPlaylistSongs:
    @respx.mock
    async def test_returns_tracks_for_multiple_entries(self):
        route = respx.get(f"{_NAVIDROME_URL}/rest/getPlaylist")
        route.mock(
            return_value=httpx.Response(
                200, json=load_fixture("navidrome/playlist-tracks")
            )
        )

        provider = _make_provider()
        tracks = await provider.get_playlist_songs(
            playlist_id="playlist-1",
            user_id="user-1",
            username="admin",
            password="adminpass",
        )

        assert len(tracks) == 2
        assert tracks[0].id == "track-1"
        assert tracks[0].track_name == "the broken hearts club"
        assert tracks[0].album_name == "the broken hearts club"
        assert tracks[0].album_id == "album-1"
        assert tracks[0].musicbrainz_id == "3c17d64c-8539-4168-9a7b-716a55309bc4"
        assert tracks[0].artists == ["gnash"]
        assert tracks[0].duration_ticks == 184 * 10_000_000
        assert tracks[0].year == "2018"
        assert tracks[1].id == "track-2"
        assert tracks[1].track_name == "drivers license"
        assert tracks[1].album_name == "SOUR (box set)"
        assert tracks[1].album_id == "album-2"
        assert tracks[1].musicbrainz_id == "143f1c88-f47f-4f37-b25d-614c74269dea"
        assert tracks[1].artists == ["Olivia Rodrigo"]
        assert tracks[1].duration_ticks == 242 * 10_000_000
        assert tracks[1].year == "2021"
        assert route.calls[0].request.url.params.get("id") == "playlist-1"

    @respx.mock
    async def test_returns_tracks_for_single_dict_entry(self):
        mocked_response = load_fixture("navidrome/playlist-tracks")
        mocked_response["subsonic-response"]["playlist"]["entry"] = mocked_response[
            "subsonic-response"
        ]["playlist"]["entry"][0]

        respx.get(f"{_NAVIDROME_URL}/rest/getPlaylist").mock(
            return_value=httpx.Response(200, json=mocked_response)
        )

        provider = _make_provider()
        tracks = await provider.get_playlist_songs(
            playlist_id="playlist-1",
            user_id="user-1",
            username="admin",
            password="adminpass",
        )

        assert len(tracks) == 1
        assert tracks[0].id == "track-1"
        assert tracks[0].track_name == "the broken hearts club"
        assert tracks[0].album_name == "the broken hearts club"
        assert tracks[0].album_id == "album-1"
        assert tracks[0].musicbrainz_id == "3c17d64c-8539-4168-9a7b-716a55309bc4"
        assert tracks[0].artists == ["gnash"]
        assert tracks[0].duration_ticks == 184 * 10_000_000
        assert tracks[0].year == "2018"

    @respx.mock
    async def test_returns_empty_when_no_entries(self):
        mocked_response = load_fixture("navidrome/playlist-tracks")
        mocked_response["subsonic-response"]["playlist"].pop("entry", None)

        respx.get(f"{_NAVIDROME_URL}/rest/getPlaylist").mock(
            return_value=httpx.Response(
                200,
                json=mocked_response,
            )
        )

        provider = _make_provider()
        tracks = await provider.get_playlist_songs(
            playlist_id="playlist-1",
            user_id="user-1",
            username="admin",
            password="adminpass",
        )

        assert tracks == []


class TestAddSongsToPlaylist:
    @respx.mock
    async def test_adds_songs(self):
        route = respx.post(f"{_NAVIDROME_URL}/rest/updatePlaylist")
        route.mock(return_value=httpx.Response(200, json=_subsonic_ok()))

        provider = _make_provider()
        result = await provider.add_songs_to_playlist(
            playlist_id="playlist-1",
            user_id="user-1",
            track_ids=["track-1", "track-2"],
            username="admin",
            password="adminpass",
        )

        assert result is None
        assert route.calls[0].request.url.params.get("playlistId") == "playlist-1"
        assert route.calls[0].request.url.params.get_list("songIdToAdd") == [
            "track-1",
            "track-2",
        ]


class TestDeleteSongsFromPlaylist:
    @respx.mock
    async def test_removes_indices_in_reverse_order(self):
        respx.get(f"{_NAVIDROME_URL}/rest/getPlaylist").mock(
            return_value=httpx.Response(
                200, json=load_fixture("navidrome/playlist-tracks")
            )
        )
        update_route = respx.post(f"{_NAVIDROME_URL}/rest/updatePlaylist")
        update_route.mock(return_value=httpx.Response(200, json=_subsonic_ok()))

        provider = _make_provider()
        result = await provider.delete_songs_from_playlist(
            playlist_id="playlist-1",
            entry_ids=["track-1", "track-2"],
            username="admin",
            password="adminpass",
        )

        assert result is None
        assert update_route.call_count == 1
        assert (
            update_route.calls[0].request.url.params.get("playlistId") == "playlist-1"
        )
        assert update_route.calls[0].request.url.params.get_list(
            "songIndexToRemove"
        ) == ["1", "0"]

    @respx.mock
    async def test_handles_single_entry(self):
        mocked_response = load_fixture("navidrome/playlist-tracks")
        mocked_response["subsonic-response"]["playlist"]["entry"] = mocked_response[
            "subsonic-response"
        ]["playlist"]["entry"][0]

        respx.get(f"{_NAVIDROME_URL}/rest/getPlaylist").mock(
            return_value=httpx.Response(200, json=mocked_response)
        )
        update_route = respx.post(f"{_NAVIDROME_URL}/rest/updatePlaylist")
        update_route.mock(return_value=httpx.Response(200, json=_subsonic_ok()))

        provider = _make_provider()
        result = await provider.delete_songs_from_playlist(
            playlist_id="playlist-1",
            entry_ids=["track-1"],
            username="admin",
            password="adminpass",
        )

        assert result is None
        assert update_route.call_count == 1
        assert update_route.calls[0].request.url.params.get_list(
            "songIndexToRemove"
        ) == ["0"]

    @respx.mock
    async def test_handles_missing_ids_gracefully(self):
        respx.get(f"{_NAVIDROME_URL}/rest/getPlaylist").mock(
            return_value=httpx.Response(
                200, json=load_fixture("navidrome/playlist-tracks")
            )
        )
        update_route = respx.post(f"{_NAVIDROME_URL}/rest/updatePlaylist")
        update_route.mock(return_value=httpx.Response(200, json=_subsonic_ok()))

        provider = _make_provider()
        result = await provider.delete_songs_from_playlist(
            playlist_id="playlist-1",
            entry_ids=["track-999"],
            username="admin",
            password="adminpass",
        )

        assert result is None
        assert update_route.call_count == 0


class TestSearchTrack:
    @respx.mock
    async def test_returns_matching_tracks(self):
        route = respx.get(f"{_NAVIDROME_URL}/rest/search3")
        route.mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/search"))
        )

        provider = _make_provider()
        tracks = await provider.search_track(
            artist_name="SZA", title="Broken Clocks", album="Broken Clocks", year="2017"
        )

        assert len(tracks) == 2
        assert tracks[0].id == "song-1"
        assert tracks[0].track_name == "Broken Clocks"
        assert tracks[0].album_name == "Broken Clocks"
        assert tracks[0].album_id == "album-1"
        assert tracks[0].musicbrainz_id == ""
        assert tracks[0].artists == ["SZA"]
        assert tracks[0].duration_ticks == 231 * 10_000_000
        assert tracks[0].year == "2017"
        assert tracks[1].id == "song-2"
        assert tracks[1].track_name == "Broken Clocks"
        assert tracks[1].album_name == "Ctrl (deluxe)"
        assert tracks[1].album_id == "album-2"
        assert tracks[1].musicbrainz_id == "e217cb7e-782a-4474-b408-e994992f41a2"
        assert tracks[1].artists == ["SZA"]
        assert tracks[1].duration_ticks == 231 * 10_000_000
        assert tracks[1].year == "2017"

        params = route.calls[0].request.url.params
        assert params.get("query") == "SZA Broken Clocks"
        assert params.get("songCount") == "10"

    @respx.mock
    async def test_wraps_single_dict_song(self):
        mocked_response = load_fixture("navidrome/search")
        mocked_response["subsonic-response"]["searchResult3"]["song"] = mocked_response[
            "subsonic-response"
        ]["searchResult3"]["song"][0]

        respx.get(f"{_NAVIDROME_URL}/rest/search3").mock(
            return_value=httpx.Response(
                200,
                json=mocked_response,
            )
        )

        provider = _make_provider()
        tracks = await provider.search_track(
            artist_name="SZA", title="Broken Clocks", album="Broken Clocks", year="2017"
        )

        assert len(tracks) == 1
        assert tracks[0].id == "song-1"
        assert tracks[0].track_name == "Broken Clocks"
        assert tracks[0].album_name == "Broken Clocks"
        assert tracks[0].album_id == "album-1"
        assert tracks[0].musicbrainz_id == ""
        assert tracks[0].artists == ["SZA"]
        assert tracks[0].duration_ticks == 231 * 10_000_000
        assert tracks[0].year == "2017"

    @respx.mock
    async def test_returns_empty_when_no_results(self):
        mocked_response = load_fixture("navidrome/search")
        mocked_response["subsonic-response"]["searchResult3"]["song"] = []

        respx.get(f"{_NAVIDROME_URL}/rest/search3").mock(
            return_value=httpx.Response(
                200,
                json=mocked_response,
            )
        )

        provider = _make_provider()
        tracks = await provider.search_track(
            artist_name="Nobody", title="Nowhere", album="Nothing", year="1900"
        )

        assert tracks == []


class TestUpdatePlaylistImage:
    @respx.mock
    async def test_noop(self):
        provider = _make_provider()

        result = await provider.update_playlist_image(
            playlist_id="playlist-1", image_url="https://example.com/cover.jpg"
        )

        assert result is None
        assert len(respx.calls) == 0


class TestRescanLibrary:
    @respx.mock
    async def test_triggers_scan(self):
        route = respx.get(f"{_NAVIDROME_URL}/rest/startScan")
        route.mock(return_value=httpx.Response(200, json=_subsonic_ok()))

        provider = _make_provider()
        result = await provider.rescan_library()

        assert result is None
        assert route.call_count == 1


class TestIsScanningLibrary:
    @respx.mock
    async def test_returns_true_when_scanning(self):
        mocked_response = load_fixture("navidrome/scan-status")
        mocked_response["subsonic-response"]["scanStatus"]["scanning"] = True

        respx.get(f"{_NAVIDROME_URL}/rest/getScanStatus").mock(
            return_value=httpx.Response(200, json=mocked_response)
        )

        provider = _make_provider()
        result = await provider.is_scanning_library()

        assert result is True

    @respx.mock
    async def test_returns_false_when_not_scanning(self):
        respx.get(f"{_NAVIDROME_URL}/rest/getScanStatus").mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/scan-status"))
        )

        provider = _make_provider()
        result = await provider.is_scanning_library()

        assert result is False


class TestWaitForRescan:
    @respx.mock
    async def test_returns_immediately_when_not_scanning(self, monkeypatch):
        mock_sleep = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", mock_sleep)

        respx.get(f"{_NAVIDROME_URL}/rest/startScan").mock(
            return_value=httpx.Response(200, json=_subsonic_ok())
        )
        respx.get(f"{_NAVIDROME_URL}/rest/getScanStatus").mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/scan-status"))
        )

        provider = _make_provider()
        result = await provider.wait_for_rescan()

        assert result is None
        mock_sleep.assert_not_awaited()

    @respx.mock
    async def test_polls_until_scan_completes(self, monkeypatch):
        mock_sleep = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", mock_sleep)

        mocked_response = load_fixture("navidrome/scan-status")
        mocked_response["subsonic-response"]["scanStatus"]["scanning"] = True

        respx.get(f"{_NAVIDROME_URL}/rest/startScan").mock(
            return_value=httpx.Response(200, json=_subsonic_ok())
        )
        scan_status_route = respx.get(f"{_NAVIDROME_URL}/rest/getScanStatus")
        scan_status_route.mock(
            side_effect=[
                httpx.Response(200, json=mocked_response),
                httpx.Response(200, json=load_fixture("navidrome/scan-status")),
            ]
        )

        provider = _make_provider()
        result = await provider.wait_for_rescan(
            poll_interval_seconds=15, max_wait_seconds=600
        )

        assert result is None
        mock_sleep.assert_awaited_once_with(15)


class TestUpdatePlaylistVisibility:
    @respx.mock
    async def test_updates_visibility(self):
        respx.post(f"{_NAVIDROME_URL}/auth/login").mock(
            return_value=httpx.Response(200, json={"token": "token-1"})
        )
        respx.get(f"{_NAVIDROME_URL}/api/user").mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/users"))
        )
        respx.get(f"{_NAVIDROME_URL}/rest/getPlaylists").mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/playlists"))
        )
        update_route = respx.post(f"{_NAVIDROME_URL}/rest/updatePlaylist")
        update_route.mock(return_value=httpx.Response(200, json=_subsonic_ok()))

        provider = _make_provider()
        result = await provider.update_playlist_visibility(
            playlist_name="Daily Recommendations",
            username="apple",
            is_public=True,
            password="adminpass",
        )

        assert result is None
        assert update_route.call_count == 1
        assert (
            update_route.calls[0].request.url.params.get("playlistId") == "playlist-1"
        )
        assert update_route.calls[0].request.url.params.get("public") == "true"

    @respx.mock
    async def test_returns_when_user_not_found(self):
        respx.post(f"{_NAVIDROME_URL}/auth/login").mock(
            return_value=httpx.Response(200, json={"token": "token-1"})
        )
        respx.get(f"{_NAVIDROME_URL}/api/user").mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/users"))
        )
        update_route = respx.post(f"{_NAVIDROME_URL}/rest/updatePlaylist")
        update_route.mock(return_value=httpx.Response(200, json=_subsonic_ok()))

        provider = _make_provider()
        result = await provider.update_playlist_visibility(
            playlist_name="Favorites",
            username="missing-user",
            is_public=True,
            password="adminpass",
        )

        assert result is None
        assert update_route.call_count == 0

    @respx.mock
    async def test_returns_when_playlist_not_found(self):
        respx.post(f"{_NAVIDROME_URL}/auth/login").mock(
            return_value=httpx.Response(200, json={"token": "token-1"})
        )
        respx.get(f"{_NAVIDROME_URL}/api/user").mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/users"))
        )
        respx.get(f"{_NAVIDROME_URL}/rest/getPlaylists").mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/playlists"))
        )
        update_route = respx.post(f"{_NAVIDROME_URL}/rest/updatePlaylist")
        update_route.mock(return_value=httpx.Response(200, json=_subsonic_ok()))

        provider = _make_provider()
        result = await provider.update_playlist_visibility(
            playlist_name="Not There",
            username="admin",
            is_public=True,
            password="adminpass",
        )

        assert result is None
        assert update_route.call_count == 0


class TestVerifyUserCredentials:
    @respx.mock
    async def test_returns_true_on_ok_status(self):
        route = respx.get(f"{_NAVIDROME_URL}/rest/ping")
        route.mock(
            return_value=httpx.Response(200, json=load_fixture("navidrome/ping"))
        )

        provider = _make_provider()
        result = await provider.verify_user_credentials("admin", "adminpass")

        assert result is True
        params = route.calls[0].request.url.params
        assert params.get("u") == "admin"
        assert params.get("f") == "json"
        assert params.get("v") == "1.16.1"

    @respx.mock
    async def test_returns_false_on_non_ok_status(self):
        mocked_response = load_fixture("navidrome/ping")
        mocked_response["subsonic-response"]["status"] = "failed"
        mocked_response["subsonic-response"]["error"] = {
            "code": 40,
            "message": "Wrong username or password",
        }

        respx.get(f"{_NAVIDROME_URL}/rest/ping").mock(
            return_value=httpx.Response(
                200,
                json=mocked_response,
            )
        )

        provider = _make_provider()
        result = await provider.verify_user_credentials("admin", "wrongpass")

        assert result is False

    @respx.mock
    async def test_returns_false_on_http_error(self):
        respx.get(f"{_NAVIDROME_URL}/rest/ping").mock(return_value=httpx.Response(500))

        provider = _make_provider()
        result = await provider.verify_user_credentials("admin", "adminpass")

        assert result is False


class TestEnsureDownloadLibraryExists:
    @respx.mock
    async def test_noop(self):
        provider = _make_provider()

        result = await provider.ensure_download_library_exists()

        assert result is None
        assert len(respx.calls) == 0
