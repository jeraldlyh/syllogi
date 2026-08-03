import asyncio

import httpx
import pytest
import respx

from lib.models.provider import ProviderError
from lib.providers.playlist.jellyfin import JellyfinProvider
from tests.lib.providers.conftest import load_fixture

_JELLYFIN_URL = "https://jellyfin.example.com"


def _make_provider() -> JellyfinProvider:
    return JellyfinProvider()


class TestGetUsers:
    @respx.mock
    async def test_returns_users(self):
        respx.get(f"{_JELLYFIN_URL}/Users").mock(
            return_value=httpx.Response(200, json=load_fixture("jellyfin/users"))
        )

        provider = _make_provider()
        users = await provider.get_users()

        assert len(users) == 2
        assert users[0].id == "user-1"
        assert users[0].name == "apple"
        assert users[1].id == "user-2"
        assert users[1].name == "berry"

    @respx.mock
    async def test_raises_on_http_error(self):
        respx.get(f"{_JELLYFIN_URL}/Users").mock(return_value=httpx.Response(500))

        provider = _make_provider()
        with pytest.raises(httpx.HTTPStatusError):
            await provider.get_users()


class TestGetUserByName:
    @respx.mock
    async def test_returns_matching_user(self):
        respx.get(f"{_JELLYFIN_URL}/Users").mock(
            return_value=httpx.Response(200, json=load_fixture("jellyfin/users"))
        )

        provider = _make_provider()
        user = await provider.get_user_by_name("apple")

        assert user is not None
        assert user.id == "user-1"
        assert user.name == "apple"

        user = await provider.get_user_by_name("berry")

        assert user is not None
        assert user.id == "user-2"
        assert user.name == "berry"

    @respx.mock
    async def test_returns_none_when_not_found(self):
        respx.get(f"{_JELLYFIN_URL}/Users").mock(
            return_value=httpx.Response(200, json=load_fixture("jellyfin/users"))
        )

        provider = _make_provider()
        user = await provider.get_user_by_name("missing-user")

        assert user is None


class TestGetPlaylists:
    @respx.mock
    async def test_returns_playlists(self):
        respx.get(f"{_JELLYFIN_URL}/Users/user-1/Items").mock(
            return_value=httpx.Response(200, json=load_fixture("jellyfin/playlists"))
        )

        provider = _make_provider()
        playlists = await provider.get_playlists(user_id="user-1")

        assert len(playlists) == 2

        assert playlists[0].id == "playlist-1"
        assert playlists[0].name == "The Daily Ketchup Podcast"

        assert playlists[1].id == "playlist-2"
        assert playlists[1].name == "Daily Recommendations"

    @respx.mock
    async def test_raises_on_http_error(self):
        respx.get(f"{_JELLYFIN_URL}/Users/user-1/Items").mock(
            return_value=httpx.Response(500)
        )

        provider = _make_provider()
        with pytest.raises(httpx.HTTPStatusError):
            await provider.get_playlists(user_id="user-1")


class TestGetOrCreatePlaylist:
    @respx.mock
    async def test_returns_existing_playlist(self):
        respx.get(f"{_JELLYFIN_URL}/Users").mock(
            return_value=httpx.Response(200, json=load_fixture("jellyfin/users"))
        )
        respx.get(f"{_JELLYFIN_URL}/Users/user-1/Items").mock(
            return_value=httpx.Response(200, json=load_fixture("jellyfin/playlists"))
        )

        provider = _make_provider()
        playlist_id, user_id = await provider.get_or_create_playlist(
            playlist_name="Daily Recommendations", username="apple"
        )

        assert playlist_id == "playlist-2"
        assert user_id == "user-1"

    @respx.mock
    async def test_creates_new_playlist_when_missing(self):
        respx.get(f"{_JELLYFIN_URL}/Users").mock(
            return_value=httpx.Response(200, json=load_fixture("jellyfin/users"))
        )
        respx.get(f"{_JELLYFIN_URL}/Users/user-1/Items").mock(
            return_value=httpx.Response(200, json=load_fixture("jellyfin/playlists"))
        )
        respx.post(f"{_JELLYFIN_URL}/Playlists").mock(
            return_value=httpx.Response(
                200, json=load_fixture("jellyfin/create-playlist")
            )
        )

        provider = _make_provider()
        playlist_id, user_id = await provider.get_or_create_playlist(
            playlist_name="New Playlist", username="apple"
        )

        assert playlist_id == "playlist-1"
        assert user_id == "user-1"

    @respx.mock
    async def test_raises_when_user_not_found(self):
        respx.get(f"{_JELLYFIN_URL}/Users").mock(
            return_value=httpx.Response(200, json=load_fixture("jellyfin/users"))
        )

        provider = _make_provider()
        with pytest.raises(ProviderError, match="Unable to find username"):
            await provider.get_or_create_playlist(
                playlist_name="Favorites", username="missing-user"
            )


class TestCreatePlaylist:
    @respx.mock
    async def test_creates_playlist(self):
        respx.post(f"{_JELLYFIN_URL}/Playlists").mock(
            return_value=httpx.Response(
                200, json=load_fixture("jellyfin/create-playlist")
            )
        )

        provider = _make_provider()
        playlist = await provider.create_playlist(
            playlist_name="New Playlist", user_id="user-1"
        )

        assert playlist.id == "playlist-1"
        assert playlist.name == "New Playlist"

    @respx.mock
    async def test_raises_on_http_error(self):
        respx.post(f"{_JELLYFIN_URL}/Playlists").mock(return_value=httpx.Response(500))

        provider = _make_provider()
        with pytest.raises(httpx.HTTPStatusError):
            await provider.create_playlist(
                playlist_name="New Playlist", user_id="user-1"
            )


class TestDeletePlaylist:
    @respx.mock
    async def test_deletes_playlist(self):
        respx.delete(f"{_JELLYFIN_URL}/Items/playlist-1").mock(
            return_value=httpx.Response(204)
        )

        provider = _make_provider()
        result = await provider.delete_playlist(playlist_id="playlist-1")

        assert result is None

    @respx.mock
    async def test_raises_on_http_error(self):
        respx.delete(f"{_JELLYFIN_URL}/Items/playlist-1").mock(
            return_value=httpx.Response(500)
        )

        provider = _make_provider()
        with pytest.raises(httpx.HTTPStatusError):
            await provider.delete_playlist(playlist_id="playlist-1")


class TestGetPlaylistSongs:
    @respx.mock
    async def test_returns_tracks(self):
        respx.get(f"{_JELLYFIN_URL}/Playlists/playlist-1/Items").mock(
            return_value=httpx.Response(
                200, json=load_fixture("jellyfin/playlist-items")
            )
        )

        provider = _make_provider()
        tracks = await provider.get_playlist_songs(
            playlist_id="playlist-1", user_id="user-1"
        )

        assert len(tracks) == 2
        assert tracks[0].id == "item-1"
        assert tracks[0].track_name == "Lose Control"
        assert tracks[0].album_name == "I’ve Tried Everything But Therapy (Part 1)"
        assert tracks[0].album_id == "album-1"
        assert tracks[0].musicbrainz_id == ""
        assert tracks[0].artists == ["Teddy Swims"]
        assert tracks[0].duration_ticks == 0
        assert tracks[0].year == "2023"

        assert tracks[1].id == "item-2"
        assert tracks[1].track_name == "What More Can I Say"
        assert tracks[1].album_name == "What More Can I Say"
        assert tracks[1].album_id == "album-2"
        assert tracks[1].musicbrainz_id == ""
        assert tracks[1].artists == ["Teddy Swims"]
        assert tracks[1].duration_ticks == 0
        assert tracks[1].year == "2023"

    @respx.mock
    async def test_raises_on_http_error(self):
        respx.get(f"{_JELLYFIN_URL}/Playlists/playlist-1/Items").mock(
            return_value=httpx.Response(500)
        )

        provider = _make_provider()
        with pytest.raises(httpx.HTTPStatusError):
            await provider.get_playlist_songs(
                playlist_id="playlist-1", user_id="user-1"
            )


class TestAddSongsToPlaylist:
    @respx.mock
    async def test_adds_songs_in_single_batch(self):
        respx.post(f"{_JELLYFIN_URL}/Playlists/playlist-1/Items").mock(
            return_value=httpx.Response(204)
        )

        provider = _make_provider()
        result = await provider.add_songs_to_playlist(
            playlist_id="playlist-1",
            user_id="user-1",
            track_ids=["track-1", "track-2"],
        )

        assert result is None

    @respx.mock
    async def test_splits_into_multiple_batches(self):
        route = respx.post(f"{_JELLYFIN_URL}/Playlists/playlist-1/Items")
        route.mock(return_value=httpx.Response(204))

        provider = _make_provider()
        await provider.add_songs_to_playlist(
            playlist_id="playlist-1",
            user_id="user-1",
            track_ids=["track-1", "track-2", "track-3"],
            batch_size=2,
        )

        assert route.call_count == 2
        assert route.calls[0].request.url.params.get("ids") == "track-1,track-2"
        assert route.calls[1].request.url.params.get("ids") == "track-3"


class TestDeleteSongsFromPlaylist:
    @respx.mock
    async def test_deletes_songs(self):
        respx.delete(f"{_JELLYFIN_URL}/Playlists/playlist-1/Items").mock(
            return_value=httpx.Response(204)
        )

        provider = _make_provider()
        result = await provider.delete_songs_from_playlist(
            playlist_id="playlist-1", entry_ids=["entry-1", "entry-2"]
        )

        assert result is None

    @respx.mock
    async def test_raises_on_http_error(self):
        respx.delete(f"{_JELLYFIN_URL}/Playlists/playlist-1/Items").mock(
            return_value=httpx.Response(500)
        )

        provider = _make_provider()
        with pytest.raises(httpx.HTTPStatusError):
            await provider.delete_songs_from_playlist(
                playlist_id="playlist-1", entry_ids=["entry-1"]
            )


class TestSearchTrack:
    @respx.mock
    async def test_returns_matching_tracks(self):
        respx.get(f"{_JELLYFIN_URL}/Items").mock(
            return_value=httpx.Response(
                200, json=load_fixture("jellyfin/search-results")
            )
        )

        provider = _make_provider()
        tracks = await provider.search_track(
            artist_name="Meghan Trainor",
            title="Still Don't Care",
            album="Toy With Me",
            year="2026",
        )

        assert len(tracks) == 1
        assert tracks[0].id == "item-1"
        assert tracks[0].track_name == "Still Don’t Care"
        assert tracks[0].album_name == "Toy With Me"
        assert tracks[0].album_id == "album-1"
        assert tracks[0].musicbrainz_id == ""
        assert tracks[0].artists == ["Meghan Trainor"]
        assert tracks[0].duration_ticks == 0
        assert tracks[0].year == "2026"

    @respx.mock
    async def test_returns_empty_list_when_no_results(self):
        respx.get(f"{_JELLYFIN_URL}/Items").mock(
            return_value=httpx.Response(200, json={"Items": []})
        )

        provider = _make_provider()
        tracks = await provider.search_track(
            artist_name="Nobody", title="Nowhere", album="Nothing", year="1900"
        )

        assert tracks == []


class TestUpdatePlaylistImage:
    @respx.mock
    async def test_noop_when_no_image_url(self):
        provider = _make_provider()

        await provider.update_playlist_image(playlist_id="playlist-1", image_url=None)
        await provider.update_playlist_image(playlist_id="playlist-1", image_url="")

        assert len(respx.calls) == 0

    @respx.mock
    async def test_updates_image_via_remote_endpoint(self):
        image_route = respx.post(
            f"{_JELLYFIN_URL}/Items/playlist-1/RemoteImages/Download"
        )
        image_route.mock(return_value=httpx.Response(204))
        primary_route = respx.post(f"{_JELLYFIN_URL}/Items/playlist-1/Images/Primary")
        primary_route.mock(return_value=httpx.Response(204))

        provider = _make_provider()
        result = await provider.update_playlist_image(
            playlist_id="playlist-1", image_url="https://example.com/cover.jpg"
        )

        assert result is None
        assert image_route.call_count == 1
        assert primary_route.call_count == 0

    @respx.mock
    async def test_falls_back_to_direct_fetch(self):
        respx.post(f"{_JELLYFIN_URL}/Items/playlist-1/RemoteImages/Download").mock(
            return_value=httpx.Response(400)
        )
        respx.get("https://example.com/cover.jpg").mock(
            return_value=httpx.Response(
                200,
                content=b"image-bytes",
                headers={"Content-Type": "image/jpeg"},
            )
        )
        primary_route = respx.post(f"{_JELLYFIN_URL}/Items/playlist-1/Images/Primary")
        primary_route.mock(return_value=httpx.Response(204))

        provider = _make_provider()
        result = await provider.update_playlist_image(
            playlist_id="playlist-1", image_url="https://example.com/cover.jpg"
        )

        assert result is None
        assert primary_route.call_count == 1


class TestRescanLibrary:
    @respx.mock
    async def test_triggers_refresh_on_download_library(self):
        respx.get(f"{_JELLYFIN_URL}/Library/MediaFolders").mock(
            return_value=httpx.Response(
                200,
                json={
                    "Items": [
                        {
                            "Name": "Downloads",
                            "Locations": ["/mnt/music/downloads"],
                            "CollectionType": "music",
                            "Id": "lib-downloads",
                            "RefreshStatus": "Idle",
                        }
                    ]
                },
            )
        )
        refresh_route = respx.post(f"{_JELLYFIN_URL}/Items/lib-downloads/Refresh")
        refresh_route.mock(return_value=httpx.Response(204))

        provider = _make_provider()
        result = await provider.rescan_library()

        assert result is None
        assert refresh_route.call_count == 1

    @respx.mock
    async def test_raises_when_download_library_not_found(self):
        respx.get(f"{_JELLYFIN_URL}/Library/MediaFolders").mock(
            return_value=httpx.Response(
                200,
                json={
                    "type": "https://tools.ietf.org/html/rfc9110#section-15.5.5",
                    "title": "Not Found",
                    "status": 404,
                    "traceId": "00-c8edc52fc1dc602dfe94be66ab271207-ff2e823e5a92f472-00",
                },
            )
        )

        provider = _make_provider()
        with pytest.raises(ProviderError, match="Media folder not found"):
            await provider.rescan_library()


class TestIsScanningLibrary:
    @respx.mock
    async def test_returns_true_when_scanning(self):
        mocked_response = load_fixture("jellyfin/virtual-folders")
        mocked_response[0]["Name"] = "Downloads"
        mocked_response[0]["RefreshStatus"] = "Active"

        respx.get(f"{_JELLYFIN_URL}/Library/VirtualFolders").mock(
            return_value=httpx.Response(200, json=mocked_response)
        )

        provider = _make_provider()
        result = await provider.is_scanning_library()

        assert result is True

    @respx.mock
    async def test_returns_false_when_not_scanning(self):
        respx.get(f"{_JELLYFIN_URL}/Library/VirtualFolders").mock(
            return_value=httpx.Response(
                200, json=load_fixture("jellyfin/virtual-folders")
            )
        )

        provider = _make_provider()
        result = await provider.is_scanning_library()

        assert result is False


class TestEnsureDownloadLibraryExists:
    @respx.mock
    async def test_noop_when_library_exists(self):
        respx.get(f"{_JELLYFIN_URL}/Library/VirtualFolders").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "Name": "Downloads",
                        "Locations": ["/mnt/music/downloads"],
                        "CollectionType": "music",
                        "ItemId": "lib-downloads",
                        "RefreshStatus": "Idle",
                    }
                ],
            )
        )
        create_route = respx.post(f"{_JELLYFIN_URL}/Library/VirtualFolders")
        create_route.mock(return_value=httpx.Response(204))

        provider = _make_provider()
        result = await provider.ensure_download_library_exists()

        assert result is None
        assert create_route.call_count == 0

    @respx.mock
    async def test_creates_library_when_missing(self):
        respx.get(f"{_JELLYFIN_URL}/Library/VirtualFolders").mock(
            return_value=httpx.Response(
                200,
                json=load_fixture("jellyfin/virtual-folders"),
            )
        )
        create_route = respx.post(f"{_JELLYFIN_URL}/Library/VirtualFolders")
        create_route.mock(return_value=httpx.Response(204))

        provider = _make_provider()
        result = await provider.ensure_download_library_exists()

        assert result is None
        assert create_route.call_count == 1


class TestWaitForRescan:
    @respx.mock
    async def test_returns_immediately_when_not_scanning(self, monkeypatch):
        async def _fail_on_sleep():
            raise AssertionError("asyncio.sleep should not be called")

        monkeypatch.setattr(asyncio, "sleep", _fail_on_sleep)

        respx.get(f"{_JELLYFIN_URL}/Library/MediaFolders").mock(
            return_value=httpx.Response(
                200,
                json={
                    "Items": [
                        {
                            "Name": "Downloads",
                            "Locations": ["/mnt/music/downloads"],
                            "CollectionType": "music",
                            "Id": "lib-downloads",
                            "RefreshStatus": "Idle",
                        }
                    ]
                },
            )
        )
        respx.post(f"{_JELLYFIN_URL}/Items/lib-downloads/Refresh").mock(
            return_value=httpx.Response(204)
        )
        respx.get(f"{_JELLYFIN_URL}/Library/VirtualFolders").mock(
            return_value=httpx.Response(
                200, json=load_fixture("jellyfin/virtual-folders")
            )
        )

        provider = _make_provider()
        result = await provider.wait_for_rescan()

        assert result is None

    @respx.mock
    async def test_polls_until_scan_completes(self, monkeypatch):
        sleep_calls = []

        async def _fake_sleep(seconds):
            sleep_calls.append(seconds)

        monkeypatch.setattr(asyncio, "sleep", _fake_sleep)

        respx.get(f"{_JELLYFIN_URL}/Library/MediaFolders").mock(
            return_value=httpx.Response(
                200,
                json={
                    "Items": [
                        {
                            "Name": "Downloads",
                            "Locations": ["/mnt/music/downloads"],
                            "CollectionType": "music",
                            "Id": "lib-downloads",
                            "RefreshStatus": "Idle",
                        }
                    ]
                },
            )
        )
        respx.post(f"{_JELLYFIN_URL}/Items/lib-downloads/Refresh").mock(
            return_value=httpx.Response(204)
        )
        scanning = [
            {
                "Name": "Downloads",
                "Locations": ["/mnt/music/downloads"],
                "CollectionType": "music",
                "ItemId": "lib-downloads",
                "RefreshStatus": "Active",
            }
        ]
        respx.get(f"{_JELLYFIN_URL}/Library/VirtualFolders").mock(
            side_effect=[
                httpx.Response(200, json=scanning),
                httpx.Response(200, json=load_fixture("jellyfin/virtual-folders")),
            ]
        )

        provider = _make_provider()
        result = await provider.wait_for_rescan(
            poll_interval_seconds=15, max_wait_seconds=600
        )

        assert result is None
        assert sleep_calls == [15]
