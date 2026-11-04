from typing import ClassVar

import pytest

from lib.spotify import get_spotify_playlist_songs


def _track_item(
    *,
    track_name="Song",
    artist_name="Artist",
    album_name="Album",
    year="2020",
    duration=180,
):
    return {
        "itemV2": {
            "__typename": "TrackResponseWrapper",
            "data": {
                "albumOfTrack": {
                    "artists": {"items": [{"profile": {"name": artist_name}}]},
                    "name": album_name,
                },
                "name": track_name,
            },
        },
        "itemV3": {
            "__typename": "TrackResponseWrapper",
            "data": {
                "identityTrait": {
                    "contentHierarchyParent": {
                        "identityTrait": {"name": album_name},
                        "publishingMetadataTrait": {
                            "firstPublishedAt": {"isoString": f"{year}-01-01T00:00:00Z"}
                        },
                    }
                },
                "consumptionExperienceTrait": {"duration": {"seconds": duration}},
            },
        },
    }


def _episode_item(*, name="Episode"):
    return {
        "itemV2": {
            "__typename": "EpisodeOrChapterResponseWrapper",
            "data": {
                "__typename": "Episode",
                "name": name,
                "episodeDuration": {"totalMilliseconds": 123000},
            },
        },
        "itemV3": {
            "__typename": "EpisodeOrChapterResponseWrapper",
            "data": {
                "identityTrait": {"contentHierarchyParent": {}},
                "consumptionExperienceTrait": {"duration": {"seconds": 123}},
            },
        },
    }


def _playlist_response(items, total_count):
    return {
        "data": {
            "playlistV2": {
                "content": {"totalCount": total_count, "items": items},
            }
        }
    }


def _fake_public_playlist(pages):
    class FakePublicPlaylist:
        calls: ClassVar[list[int]] = []

        def __init__(self, playlist_id):
            self.playlist_id = playlist_id

        def get_playlist_info(self, limit=25, *, offset=0):
            self.calls.append(offset)
            return pages.get(offset, _playlist_response([], 0))

    return FakePublicPlaylist


@pytest.fixture(autouse=True)
def _clear_spotify_cache():
    get_spotify_playlist_songs.cache.clear()  # type: ignore[attr-defined]
    yield
    get_spotify_playlist_songs.cache.clear()  # type: ignore[attr-defined]


class TestGetSpotifyPlaylistSongs:
    def test_skips_episode_without_album_of_track(self, monkeypatch):
        fake = _fake_public_playlist(
            {
                0: _playlist_response(
                    [_episode_item(), _track_item(track_name="Keep Me")], 2
                )
            }
        )
        monkeypatch.setattr("lib.spotify.PublicPlaylist", fake)

        songs = get_spotify_playlist_songs("playlist-with-episode")

        assert [song.track_name for song in songs] == ["Keep Me"]
        assert songs[0].artist_name == "Artist"
        assert songs[0].album_name == "Album"
        assert songs[0].year == "2020"
        assert songs[0].duration == 180

    def test_skips_episodes_across_paginated_pages(self, monkeypatch):
        first_page = [_episode_item()] + [
            _track_item(track_name=f"Song {i}") for i in range(49)
        ]
        second_page = [_track_item(track_name="Last Song"), _episode_item()]
        fake = _fake_public_playlist(
            {
                0: _playlist_response(first_page, 52),
                50: _playlist_response(second_page, 52),
            }
        )
        monkeypatch.setattr("lib.spotify.PublicPlaylist", fake)

        songs = get_spotify_playlist_songs("paginated-playlist")

        assert len(songs) == 50
        assert songs[0].track_name == "Song 0"
        assert songs[-1].track_name == "Last Song"
        assert fake.calls == [0, 50, 100]

    def test_track_missing_album_of_track_still_raises(self, monkeypatch):
        malformed_track = _track_item()
        del malformed_track["itemV2"]["data"]["albumOfTrack"]

        fake = _fake_public_playlist({0: _playlist_response([malformed_track], 1)})
        monkeypatch.setattr("lib.spotify.PublicPlaylist", fake)

        with pytest.raises(KeyError):
            get_spotify_playlist_songs("malformed-playlist")
