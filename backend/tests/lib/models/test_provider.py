import pytest

from lib.models.provider import (
    ProviderError,
    ProviderPlaylist,
    ProviderTrack,
    ProviderUser,
)


def _make_provider_user(**overrides) -> ProviderUser:
    defaults = {"id": "u-1", "name": "Alice"}
    defaults.update(overrides)
    return ProviderUser(**defaults)


def _make_provider_track(**overrides) -> ProviderTrack:
    defaults = {
        "id": "t-1",
        "track_name": "Song",
        "album_name": "Album",
        "album_id": "al-1",
        "musicbrainz_id": "mb-1",
        "artists": ["Artist A", "Artist B"],
        "duration_ticks": 10000000,
        "year": "2024",
    }
    defaults.update(overrides)
    return ProviderTrack(**defaults)


def _make_provider_playlist(**overrides) -> ProviderPlaylist:
    defaults = {"id": "p-1", "name": "Playlist", "owner_id": "u-1"}
    defaults.update(overrides)
    return ProviderPlaylist(**defaults)


class TestProviderError:
    def test_is_exception(self):
        with pytest.raises(ProviderError):
            raise ProviderError("something went wrong")

    def test_message(self):
        err = ProviderError("test message")

        assert str(err) == "test message"


class TestProviderUser:
    def test_defaults(self):
        user = _make_provider_user()

        assert user.id == "u-1"
        assert user.name == "Alice"

    def test_to_dict(self):
        user = _make_provider_user()

        assert user.to_dict() == {"id": "u-1", "name": "Alice"}


class TestProviderTrack:
    def test_defaults(self):
        track = _make_provider_track()

        assert track.id == "t-1"
        assert track.artists == ["Artist A", "Artist B"]

    def test_is_not_found_true(self):
        track = _make_provider_track(id="")

        assert track.is_not_found() is True

    def test_is_not_found_false(self):
        track = _make_provider_track()

        assert track.is_not_found() is False

    def test_to_dict(self):
        track = _make_provider_track()
        data = track.to_dict()

        assert data["id"] == "t-1"
        assert data["track_name"] == "Song"
        assert data["artists"] == ["Artist A", "Artist B"]
        assert data["duration_ticks"] == 10000000


class TestProviderPlaylist:
    def test_defaults(self):
        playlist = _make_provider_playlist()

        assert playlist.id == "p-1"
        assert playlist.owner_id == "u-1"

    def test_to_dict(self):
        playlist = _make_provider_playlist()

        assert playlist.to_dict() == {
            "id": "p-1",
            "name": "Playlist",
            "owner_id": "u-1",
        }
