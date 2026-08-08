from lib.models.jellyfin import (
    JellyfinLibrary,
    JellyfinPlaylist,
    JellyfinTrack,
    JellyfinUser,
)


def _make_jellyfin_user(**overrides) -> JellyfinUser:
    defaults = {"id": "j-1", "name": "Alice"}
    defaults.update(overrides)
    return JellyfinUser(**defaults)


def _make_jellyfin_track(**overrides) -> JellyfinTrack:
    defaults = {
        "id": "j-1",
        "track_name": "Song",
        "album_name": "Album",
        "album_id": "a-1",
        "musicbrainz_id": "mb-1",
        "artists": ["Artist"],
        "duration_ticks": 50000,
        "year": "2024",
    }
    defaults.update(overrides)
    return JellyfinTrack(**defaults)


def _make_jellyfin_playlist(**overrides) -> JellyfinPlaylist:
    defaults = {"id": "jp-1", "name": "My Playlist", "owner_id": "j-1"}
    defaults.update(overrides)
    return JellyfinPlaylist(**defaults)


def _make_jellyfin_library(**overrides) -> JellyfinLibrary:
    defaults = {
        "name": "Music",
        "locations": ["/music"],
        "collection_type": "music",
        "item_id": "lib-1",
        "refresh_status": "completed",
    }
    defaults.update(overrides)
    return JellyfinLibrary(**defaults)


class TestJellyfinUser:
    def test_to_dict(self):
        user = _make_jellyfin_user()
        assert user.to_dict() == {"id": "j-1", "name": "Alice"}


class TestJellyfinTrack:
    def test_is_not_found_true_empty(self):
        track = _make_jellyfin_track(
            id="", track_name="T", album_name="A", artists=[], duration_ticks=0, year=""
        )

        assert track.is_not_found() is True

    def test_is_not_found_false(self):
        track = _make_jellyfin_track(
            track_name="T", album_name="A", artists=["Art"], duration_ticks=100
        )

        assert track.is_not_found() is False

    def test_to_dict(self):
        track = _make_jellyfin_track()
        data = track.to_dict()

        assert data["id"] == "j-1"
        assert data["track_name"] == "Song"
        assert data["artists"] == ["Artist"]
        assert data["duration_ticks"] == 50000


class TestJellyfinPlaylist:
    def test_to_dict(self):
        playlist = _make_jellyfin_playlist()

        assert playlist.to_dict() == {
            "id": "jp-1",
            "name": "My Playlist",
            "owner_id": "j-1",
        }


class TestJellyfinLibrary:
    def test_to_dict(self):
        lib = _make_jellyfin_library()
        data = lib.to_dict()

        assert data["name"] == "Music"
        assert data["locations"] == ["/music"]
        assert data["collection_type"] == "music"
