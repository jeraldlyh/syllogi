import inspect
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from lib import library
from lib.library import (
    filter_tracks,
    invalidate_track,
    read_library_track,
    resolve_library_path,
    scan_library,
    summarize_library,
)
from lib.models.library import AudioTags, LibraryTrack


@pytest.fixture(autouse=True)
def clear_library_caches():
    """Start every test from a cold library, so cached scans do not leak between them."""

    library._scan_cache = None
    library._track_cache.clear()
    yield
    library._scan_cache = None
    library._track_cache.clear()


def make_track(
    path: str = "Artist/Album/Track.flac",
    file_format: str = "flac",
    has_lyrics: bool = True,
    **tag_overrides,
) -> LibraryTrack:
    tags = AudioTags(
        title="Blinding Lights",
        artist="The Weeknd",
        album="After Hours",
        date="2020",
        genres=["synth-pop"],
        lyrics="Yeah" if has_lyrics else "",
        musicbrainz_id="9b1a2b3c",
    )

    for key, value in tag_overrides.items():
        setattr(tags, key, value)

    return LibraryTrack(
        path=path,
        filename=Path(path).name,
        directory=str(Path(path).parent),
        format=file_format,
        size=1024,
        duration=200,
        tags=tags,
        has_lyrics=has_lyrics,
    )


class TestIsSyncedLyrics:
    def test_returns_true_for_lrc_timestamps(self):
        track = make_track(lyrics="[00:12.34] I've been tryna call")

        assert track.is_synced_lyrics() is True

    def test_returns_false_for_plain_lyrics(self):
        track = make_track(lyrics="I've been tryna call\nFor a while now")

        assert track.is_synced_lyrics() is False

    def test_returns_false_for_empty_lyrics(self):
        track = make_track(lyrics="")

        assert track.is_synced_lyrics() is False


class TestResolveLibraryPath:
    @patch("lib.library.get_library_directory")
    def test_rejects_paths_outside_the_library(self, mock_directory, tmp_path):
        mock_directory.return_value = tmp_path

        with pytest.raises(HTTPException) as error:
            resolve_library_path("../escaped.flac")

        assert error.value.status_code == 400

    @patch("lib.library.get_library_directory")
    def test_rejects_unsupported_formats(self, mock_directory, tmp_path):
        mock_directory.return_value = tmp_path
        (tmp_path / "cover.jpg").write_bytes(b"")

        with pytest.raises(HTTPException) as error:
            resolve_library_path("cover.jpg")

        assert error.value.status_code == 400

    @patch("lib.library.get_library_directory")
    def test_rejects_missing_files(self, mock_directory, tmp_path):
        mock_directory.return_value = tmp_path

        with pytest.raises(HTTPException) as error:
            resolve_library_path("Artist/Missing.flac")

        assert error.value.status_code == 404

    @patch("lib.library.get_library_directory")
    def test_returns_the_resolved_path(self, mock_directory, tmp_path):
        mock_directory.return_value = tmp_path
        track = tmp_path / "Artist" / "Track.flac"
        track.parent.mkdir(parents=True)
        track.write_bytes(b"")

        assert resolve_library_path("Artist/Track.flac") == track


class TestReadLibraryTrack:
    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_reads_tags_into_a_library_track(self, mock_directory, mock_read, tmp_path):
        mock_directory.return_value = tmp_path
        track_path = tmp_path / "The Weeknd" / "After Hours" / "Blinding Lights.flac"
        track_path.parent.mkdir(parents=True)
        track_path.write_bytes(b"x" * 32)
        mock_read.return_value = (
            AudioTags(title="Blinding Lights", lyrics="[00:01.00] Yeah"),
            200,
        )
        invalidate_track("The Weeknd/After Hours/Blinding Lights.flac")

        track = read_library_track(track_path)

        assert track is not None
        assert track.path == "The Weeknd/After Hours/Blinding Lights.flac"
        assert track.filename == "Blinding Lights.flac"
        assert track.directory == "The Weeknd/After Hours"
        assert track.format == "flac"
        assert track.size == 32
        assert track.duration == 200
        assert track.has_lyrics is True
        assert track.is_synced_lyrics() is True

    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_returns_none_when_tags_cannot_be_read(
        self, mock_directory, mock_read, tmp_path
    ):
        mock_directory.return_value = tmp_path
        track_path = tmp_path / "Broken.flac"
        track_path.write_bytes(b"")
        mock_read.return_value = None
        invalidate_track("Broken.flac")

        assert read_library_track(track_path) is None

    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_serves_unchanged_files_from_the_cache(
        self, mock_directory, mock_read, tmp_path
    ):
        mock_directory.return_value = tmp_path
        track_path = tmp_path / "Cached.flac"
        track_path.write_bytes(b"")
        mock_read.return_value = (AudioTags(title="Cached"), 100)
        invalidate_track("Cached.flac")

        read_library_track(track_path)
        read_library_track(track_path)

        assert mock_read.call_count == 1


class TestScanLibrary:
    @patch("lib.library.get_library_directory")
    def test_returns_nothing_when_the_directory_is_missing(
        self, mock_directory, tmp_path
    ):
        mock_directory.return_value = tmp_path / "absent"

        assert scan_library() == []

    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_finds_supported_files_and_skips_the_rest(
        self, mock_directory, mock_read, tmp_path
    ):
        mock_directory.return_value = tmp_path
        (tmp_path / "Artist").mkdir()
        (tmp_path / "Artist" / "Track.flac").write_bytes(b"")
        (tmp_path / "Artist" / "Track.mp3").write_bytes(b"")
        (tmp_path / "Artist" / "cover.jpg").write_bytes(b"")
        mock_read.return_value = (AudioTags(title="Track"), 100)

        tracks = scan_library()

        assert [track.path for track in tracks] == [
            "Artist/Track.flac",
            "Artist/Track.mp3",
        ]


class TestScanLibraryCaching:
    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_repeat_scans_do_not_rewalk_the_directory(
        self, mock_directory, mock_read, tmp_path
    ):
        mock_directory.return_value = tmp_path
        (tmp_path / "Track.flac").write_bytes(b"")
        mock_read.return_value = (AudioTags(title="Track"), 100)

        with patch("lib.library._walk_library", wraps=library._walk_library) as walk:
            scan_library()
            scan_library()
            scan_library()

        assert walk.call_count == 1

    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_writing_a_file_forces_the_next_scan_to_rewalk(
        self, mock_directory, mock_read, tmp_path
    ):
        mock_directory.return_value = tmp_path
        (tmp_path / "Track.flac").write_bytes(b"")
        mock_read.return_value = (AudioTags(title="Track"), 100)

        with patch("lib.library._walk_library", wraps=library._walk_library) as walk:
            scan_library()
            invalidate_track("Track.flac")
            scan_library()

        assert walk.call_count == 2


class TestRouteHandlersStayOffTheEventLoop:
    """The library routes block on disk I/O for as long as the walk takes.

    Declaring them `async def` puts that blocking work on the event loop and
    stalls every other request until the scan finishes, which reads as the whole
    server hanging. FastAPI runs plain `def` handlers in a worker thread instead.
    """

    @pytest.mark.parametrize(
        "handler_name",
        ["_list_library_tracks", "_get_library_track", "_update_library_track"],
    )
    def test_file_io_handlers_are_not_coroutines(self, handler_name):
        import routes.library

        handler = getattr(routes.library, handler_name)

        assert not inspect.iscoroutinefunction(handler)

    @pytest.mark.parametrize("handler_name", ["_search_lyrics", "_search_recordings"])
    def test_network_handlers_stay_async(self, handler_name):
        import routes.library

        handler = getattr(routes.library, handler_name)

        assert inspect.iscoroutinefunction(handler)


class TestFilterTracks:
    def test_matches_free_text_against_tags_and_filenames(self):
        tracks = [
            make_track(),
            make_track(path="Other/Other/Other.flac", title="Other"),
        ]

        results = filter_tracks(tracks, query="weeknd")

        assert len(results) == 2

        results = filter_tracks(tracks, query="blinding")

        assert len(results) == 1

    def test_filters_by_format(self):
        tracks = [make_track(), make_track(path="A/B/C.mp3", file_format="mp3")]

        results = filter_tracks(tracks, file_format="mp3")

        assert [track.format for track in results] == ["mp3"]

    def test_filters_by_missing_lyrics(self):
        tracks = [make_track(), make_track(path="A/B/C.flac", has_lyrics=False)]

        results = filter_tracks(tracks, missing="lyrics")

        assert [track.path for track in results] == ["A/B/C.flac"]

    def test_filters_by_missing_musicbrainz_id(self):
        tracks = [make_track(), make_track(path="A/B/C.flac", musicbrainz_id="")]

        results = filter_tracks(tracks, missing="musicbrainz_id")

        assert [track.path for track in results] == ["A/B/C.flac"]

    def test_filters_by_any_missing_tag(self):
        tracks = [make_track(), make_track(path="A/B/C.flac", album="")]

        results = filter_tracks(tracks, missing="any")

        assert [track.path for track in results] == ["A/B/C.flac"]


class TestSummarizeLibrary:
    def test_counts_the_gaps_worth_acting_on(self):
        tracks = [
            make_track(),
            make_track(path="A/B/C.mp3", file_format="mp3", has_lyrics=False),
            make_track(path="A/B/D.flac", musicbrainz_id=""),
        ]

        assert summarize_library(tracks) == {
            "total": 3,
            "missing_lyrics": 1,
            "missing_musicbrainz_id": 1,
            "lossless": 2,
        }


class TestLibraryTrackSerialization:
    def test_omits_lyrics_from_list_responses(self):
        payload = make_track().to_dict()

        assert "lyrics" not in payload["tags"]

    def test_includes_lyrics_when_asked(self):
        payload = make_track().to_dict(include_lyrics=True)

        assert payload["tags"]["lyrics"] == "Yeah"

    def test_reports_which_fields_carry_a_value(self):
        track = make_track(album="", musicbrainz_id="")

        assert track.filled_fields() == ["title", "artist", "date", "genres", "lyrics"]


class TestAudioTagsSerialization:
    def test_round_trips_every_field(self):
        tags = AudioTags(
            title="Blinding Lights",
            artist="The Weeknd",
            album="After Hours",
            date="2020",
            genres=["synth-pop"],
            lyrics="Yeah",
            musicbrainz_id="9b1a2b3c",
        )

        assert tags.to_dict() == {
            "title": "Blinding Lights",
            "artist": "The Weeknd",
            "album": "After Hours",
            "date": "2020",
            "genres": ["synth-pop"],
            "lyrics": "Yeah",
            "musicbrainz_id": "9b1a2b3c",
        }


class TestReadIdTagsFallback:
    def test_reads_the_musicbrainz_id_from_a_txxx_frame(self):
        from lib.tagger import _read_id3_tags

        txxx = MagicMock()
        txxx.desc = "MusicBrainz Track Id"
        txxx.text = ["9b1a2b3c"]
        tags = MagicMock()
        tags.get.return_value = None
        tags.getall.side_effect = lambda key: [txxx] if key == "TXXX" else []

        assert _read_id3_tags(tags).musicbrainz_id == "9b1a2b3c"
