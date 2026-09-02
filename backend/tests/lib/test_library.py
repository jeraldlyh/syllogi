import inspect
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine

from db.library import get_track_fingerprints, summarize_library
from db.models.library import LibraryTrack
from lib import library
from lib.library import (
    delete_empty_folders,
    read_library_track,
    resolve_library_folder,
    resolve_library_path,
    sweep_library,
    trigger_library_sweep,
    walk_library,
)
from lib.models.library import AudioTags


@pytest.fixture(autouse=True)
def reset_sweep_state():
    library._sweeping = False
    library._last_swept_at = None
    library._last_swept_on = None
    library._last_error = None
    yield
    library._sweeping = False
    library._last_swept_at = None


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


def make_track(
    path: str = "Artist/Album/Track.flac",
    file_format: str = "flac",
    **overrides,
) -> LibraryTrack:
    track = LibraryTrack(
        path=path,
        filename=Path(path).name,
        directory=str(Path(path).parent),
        format=file_format,
        size=1024,
        duration=200,
        mtime=1.0,
        title="Blinding Lights",
        artist="The Weeknd",
        album="After Hours",
        date="2020",
        genres=["synth-pop"],
        musicbrainz_id="9b1a2b3c",
        has_lyrics=True,
        is_synced_lyrics=False,
    )

    for key, value in overrides.items():
        setattr(track, key, value)

    return track


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

        result = read_library_track(track_path)

        assert result is not None
        track, lyrics = result
        assert track.path == "The Weeknd/After Hours/Blinding Lights.flac"
        assert track.filename == "Blinding Lights.flac"
        assert track.directory == "The Weeknd/After Hours"
        assert track.format == "flac"
        assert track.size == 32
        assert track.duration == 200
        assert track.has_lyrics is True
        assert track.is_synced_lyrics is True
        assert track.mtime == track_path.stat().st_mtime
        assert lyrics == "[00:01.00] Yeah"

    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_returns_the_lyrics_body_without_storing_it(
        self, mock_directory, mock_read, tmp_path
    ):
        """Lyrics ride alongside the row for the editor, but never onto it."""

        mock_directory.return_value = tmp_path
        track_path = tmp_path / "Track.flac"
        track_path.write_bytes(b"")
        mock_read.return_value = (AudioTags(title="Track", lyrics="Yeah"), 100)

        result = read_library_track(track_path)

        assert result is not None
        track, lyrics = result
        assert lyrics == "Yeah"
        assert not hasattr(track, "lyrics")

    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_stores_names_in_composed_form(self, mock_directory, mock_read, tmp_path):
        """SMB hands back decomposed names; the row must hold the composed one."""

        mock_directory.return_value = tmp_path
        decomposed = "아이".encode().decode()
        track_path = tmp_path / f"{decomposed}.flac"
        track_path.write_bytes(b"")
        mock_read.return_value = (AudioTags(title="한"), 100)

        result = read_library_track(track_path)

        assert result is not None
        assert result[0].title == "한"

    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_reports_which_tag_fields_are_filled(
        self, mock_directory, mock_read, tmp_path
    ):
        mock_directory.return_value = tmp_path
        track_path = tmp_path / "Track.flac"
        track_path.write_bytes(b"")
        mock_read.return_value = (AudioTags(title="Track", artist="Someone"), 100)

        result = read_library_track(track_path)

        assert result is not None
        assert result[0].filled_fields() == ["title", "artist"]

    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_returns_none_when_tags_cannot_be_read(
        self, mock_directory, mock_read, tmp_path
    ):
        mock_directory.return_value = tmp_path
        track_path = tmp_path / "Broken.flac"
        track_path.write_bytes(b"")
        mock_read.return_value = None

        assert read_library_track(track_path) is None

    @patch("lib.library.get_library_directory")
    def test_returns_none_when_the_file_is_gone(self, mock_directory, tmp_path):
        mock_directory.return_value = tmp_path

        assert read_library_track(tmp_path / "Absent.flac") is None


class TestWalkLibrary:
    @patch("lib.library.get_library_directory")
    def test_returns_nothing_when_the_directory_is_missing(
        self, mock_directory, tmp_path
    ):
        mock_directory.return_value = tmp_path / "absent"

        assert walk_library() == ({}, [])

    @patch("lib.library.get_library_directory")
    def test_stats_supported_files_and_skips_the_rest(self, mock_directory, tmp_path):
        mock_directory.return_value = tmp_path
        (tmp_path / "Artist").mkdir()
        (tmp_path / "Artist" / "Track.flac").write_bytes(b"xyz")
        (tmp_path / "Artist" / "Track.mp3").write_bytes(b"")
        (tmp_path / "Artist" / "cover.jpg").write_bytes(b"")

        files, _ = walk_library()

        assert sorted(files) == ["Artist/Track.flac", "Artist/Track.mp3"]
        assert files["Artist/Track.flac"][1] == 3

    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_does_not_read_tags(self, mock_directory, mock_read, tmp_path):
        """The walk is stat-only; opening a file on a share costs far more."""

        mock_directory.return_value = tmp_path
        (tmp_path / "Track.flac").write_bytes(b"")

        walk_library()

        mock_read.assert_not_called()

    @patch("lib.library.get_library_directory")
    def test_reports_folders_holding_no_audio(self, mock_directory, tmp_path):
        mock_directory.return_value = tmp_path
        (tmp_path / "Artist").mkdir()
        (tmp_path / "Artist" / "Track.flac").write_bytes(b"")
        (tmp_path / "Abandoned").mkdir()
        (tmp_path / "Artwork Only").mkdir()
        (tmp_path / "Artwork Only" / "cover.jpg").write_bytes(b"")

        _, empty = walk_library()

        assert empty == ["Abandoned", "Artwork Only"]

    @patch("lib.library.get_library_directory")
    def test_reports_only_the_outermost_dead_folder(self, mock_directory, tmp_path):
        mock_directory.return_value = tmp_path
        (tmp_path / "Artist" / "Album").mkdir(parents=True)

        _, empty = walk_library()

        assert empty == ["Artist"]

    @patch("lib.library.get_library_directory")
    def test_keeps_a_folder_whose_audio_sits_in_a_subfolder(
        self, mock_directory, tmp_path
    ):
        mock_directory.return_value = tmp_path
        (tmp_path / "Artist" / "Album").mkdir(parents=True)
        (tmp_path / "Artist" / "Album" / "Track.flac").write_bytes(b"")

        _, empty = walk_library()

        assert empty == []


class TestDeleteEmptyFolders:
    @staticmethod
    def _sweep(session) -> None:
        with patch("lib.library.read_audio_tags", return_value=(AudioTags(), 100)):
            sweep_library(session)

    @patch("lib.library.get_library_directory")
    def test_deletes_the_folders_the_sweep_found(
        self, mock_directory, tmp_path, session
    ):
        mock_directory.return_value = tmp_path
        (tmp_path / "Artist").mkdir()
        (tmp_path / "Artist" / "Track.flac").write_bytes(b"")
        (tmp_path / "Abandoned" / "Album").mkdir(parents=True)
        self._sweep(session)

        result = delete_empty_folders(session)

        assert result["deleted"] == ["Abandoned"]
        assert result["kept"] == []
        assert not (tmp_path / "Abandoned").exists()
        assert (tmp_path / "Artist" / "Track.flac").exists()

    @patch("lib.library.get_library_directory")
    def test_takes_non_audio_leftovers_with_the_folder(
        self, mock_directory, tmp_path, session
    ):
        mock_directory.return_value = tmp_path
        (tmp_path / "Artwork Only").mkdir()
        (tmp_path / "Artwork Only" / "cover.jpg").write_bytes(b"")
        self._sweep(session)

        assert delete_empty_folders(session)["deleted"] == ["Artwork Only"]
        assert not (tmp_path / "Artwork Only").exists()

    @patch("lib.library.get_library_directory")
    def test_keeps_a_folder_that_gained_audio_since_the_sweep(
        self, mock_directory, tmp_path, session
    ):
        mock_directory.return_value = tmp_path
        (tmp_path / "Abandoned").mkdir()
        self._sweep(session)
        (tmp_path / "Abandoned" / "Track.flac").write_bytes(b"")

        result = delete_empty_folders(session)

        assert result["deleted"] == []
        assert result["kept"] == ["Abandoned"]
        assert (tmp_path / "Abandoned" / "Track.flac").exists()

    @patch("lib.library.get_library_directory")
    def test_clears_the_stored_list_once_the_folders_are_gone(
        self, mock_directory, tmp_path, session
    ):
        mock_directory.return_value = tmp_path
        (tmp_path / "Abandoned").mkdir()
        self._sweep(session)

        delete_empty_folders(session)

        assert summarize_library(session)["empty_directories"] == 0

    @patch("lib.library.get_library_directory")
    def test_ignores_a_folder_deleted_outside_the_app(
        self, mock_directory, tmp_path, session
    ):
        mock_directory.return_value = tmp_path
        (tmp_path / "Abandoned").mkdir()
        self._sweep(session)
        (tmp_path / "Abandoned").rmdir()

        result = delete_empty_folders(session)

        assert result["deleted"] == []
        assert result["kept"] == []


class TestResolveLibraryFolder:
    @patch("lib.library.get_library_directory")
    def test_refuses_a_path_outside_the_library(self, mock_directory, tmp_path):
        mock_directory.return_value = tmp_path / "library"
        (tmp_path / "library").mkdir()
        (tmp_path / "outside").mkdir()

        assert resolve_library_folder("../outside") is None

    @patch("lib.library.get_library_directory")
    def test_refuses_the_library_root(self, mock_directory, tmp_path):
        mock_directory.return_value = tmp_path

        assert resolve_library_folder("") is None

    @patch("lib.library.get_library_directory")
    def test_refuses_a_file(self, mock_directory, tmp_path):
        mock_directory.return_value = tmp_path
        (tmp_path / "Track.flac").write_bytes(b"")

        assert resolve_library_folder("Track.flac") is None

    @patch("lib.library.get_library_directory")
    def test_returns_the_folder(self, mock_directory, tmp_path):
        mock_directory.return_value = tmp_path
        (tmp_path / "Artist").mkdir()

        assert resolve_library_folder("Artist") == tmp_path / "Artist"


class TestSweepLibrary:
    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_fills_an_empty_library(self, mock_directory, mock_read, tmp_path, session):
        mock_directory.return_value = tmp_path
        (tmp_path / "Artist").mkdir()
        (tmp_path / "Artist" / "Track.flac").write_bytes(b"")
        (tmp_path / "Dead").mkdir()
        mock_read.return_value = (AudioTags(title="Track"), 100)

        result = sweep_library(session)

        assert result["total"] == 1
        assert result["read"] == 1
        assert summarize_library(session)["total"] == 1
        assert summarize_library(session)["empty_directories"] == 1

    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_reads_only_files_whose_fingerprint_moved(
        self, mock_directory, mock_read, tmp_path, session
    ):
        mock_directory.return_value = tmp_path
        (tmp_path / "One.flac").write_bytes(b"")
        (tmp_path / "Two.flac").write_bytes(b"")
        mock_read.return_value = (AudioTags(title="Track"), 100)

        sweep_library(session)
        mock_read.reset_mock()

        result = sweep_library(session)

        assert result["read"] == 0
        assert mock_read.call_count == 0

    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_rereads_a_file_whose_size_changed(
        self, mock_directory, mock_read, tmp_path, session
    ):
        mock_directory.return_value = tmp_path
        track = tmp_path / "One.flac"
        track.write_bytes(b"")
        mock_read.return_value = (AudioTags(title="Track"), 100)

        sweep_library(session)
        track.write_bytes(b"changed")
        mock_read.reset_mock()

        assert sweep_library(session)["read"] == 1

    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_drops_rows_for_files_that_vanished(
        self, mock_directory, mock_read, tmp_path, session
    ):
        mock_directory.return_value = tmp_path
        (tmp_path / "One.flac").write_bytes(b"")
        (tmp_path / "Two.flac").write_bytes(b"")
        mock_read.return_value = (AudioTags(title="Track"), 100)

        sweep_library(session)
        (tmp_path / "Two.flac").unlink()

        result = sweep_library(session)

        assert result["removed"] == 1
        assert sorted(get_track_fingerprints(session)) == ["One.flac"]

    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_counts_files_it_could_not_read(
        self, mock_directory, mock_read, tmp_path, session
    ):
        mock_directory.return_value = tmp_path
        (tmp_path / "Broken.flac").write_bytes(b"")
        mock_read.return_value = None

        result = sweep_library(session)

        assert result["unreadable"] == 1
        assert summarize_library(session)["total"] == 0

    @patch("lib.library.read_audio_tags")
    @patch("lib.library.get_library_directory")
    def test_refreshes_empty_folders_rather_than_accumulating_them(
        self, mock_directory, mock_read, tmp_path, session
    ):
        mock_directory.return_value = tmp_path
        (tmp_path / "Dead").mkdir()
        mock_read.return_value = (AudioTags(title="Track"), 100)

        sweep_library(session)
        (tmp_path / "Dead" / "Track.flac").write_bytes(b"")

        sweep_library(session)

        assert summarize_library(session)["empty_directories"] == 0


class TestTriggerLibrarySweep:
    def test_refuses_to_start_a_second_sweep_while_one_runs(self):
        library._sweeping = True

        assert trigger_library_sweep() is False

    def test_skips_a_sweep_while_the_last_one_is_still_fresh(self):
        import time

        library._last_swept_at = time.monotonic()

        assert trigger_library_sweep() is False

    def test_forces_a_sweep_past_the_freshness_window(self):
        import time

        library._last_swept_at = time.monotonic()

        with patch("lib.library.threading.Thread") as thread:
            assert trigger_library_sweep(force=True) is True

        thread.assert_called_once()

    def test_reports_the_scan_state(self):
        state = library.get_scan_state()

        assert state == {"scanning": False, "last_scanned_at": None, "error": None}


class TestRouteHandlersStayOffTheEventLoop:
    """The single-file library routes block on disk I/O for as long as the read takes.

    Declaring them `async def` puts that blocking work on the event loop and
    stalls every other request until it finishes, which reads as the whole
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

    @pytest.mark.parametrize(
        "handler_name", ["_search_lyrics", "_search_recordings", "_scan_library"]
    )
    def test_handlers_that_never_touch_disk_stay_async(self, handler_name):
        import routes.library

        handler = getattr(routes.library, handler_name)

        assert inspect.iscoroutinefunction(handler)


class TestLibraryTrackSerialization:
    def test_omits_lyrics_from_list_responses(self):
        payload = make_track().to_dict()

        assert "lyrics" not in payload["tags"]

    def test_includes_lyrics_when_given(self):
        payload = make_track().to_dict(lyrics="Yeah")

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
