from lib.models.slskd import (
    SlskdDownloadDirectory,
    SlskdDownloadFile,
    SlskdDownloadResult,
    SlskdSearchFile,
    SlskdSearchStatus,
    SlskdTrackCandidate,
)


def _make_search_status(**overrides) -> SlskdSearchStatus:
    defaults = {
        "id": "s-1",
        "search_text": "query",
        "state": "Complete",
        "token": 0,
        "file_count": 10,
        "locked_file_count": 3,
        "response_count": 5,
        "is_complete": True,
        "started_at": "2024-01-01",
        "ended_at": None,
    }
    defaults.update(overrides)
    return SlskdSearchStatus(**defaults)


def _make_search_file(**overrides) -> SlskdSearchFile:
    defaults = {
        "filename": "song.flac",
        "size": 1000,
        "is_locked": False,
        "length": None,
        "sample_rate": None,
        "bit_depth": None,
    }
    defaults.update(overrides)
    return SlskdSearchFile(**defaults)


def _make_download_file(**overrides) -> SlskdDownloadFile:
    defaults = {
        "id": "d-1",
        "username": "user1",
        "direction": "download",
        "filename": "song.flac",
        "size": 1000,
        "start_offset": 0,
        "state": "Completed, Succeeded",
        "state_description": "",
        "requested_at": "",
        "enqueued_at": "",
        "started_at": "",
        "ended_at": "",
        "bytes_transferred": 1000,
        "average_speed": 0,
        "bytes_remaining": 0,
        "elapsed_time": "",
        "percent_complete": 100,
        "remaining_time": "",
        "local_path": "",
    }
    defaults.update(overrides)
    return SlskdDownloadFile(**defaults)


class TestSlskdSearchStatus:
    def test_has_available_files_true(self):
        status = _make_search_status()

        assert status.has_available_files() is True

    def test_has_available_files_false_all_locked(self):
        status = _make_search_status(locked_file_count=10)

        assert status.has_available_files() is False

    def test_has_available_files_false_no_files(self):
        status = _make_search_status(
            file_count=0, locked_file_count=0, response_count=0
        )

        assert status.has_available_files() is False

    def test_to_dict(self):
        status = _make_search_status(token=42, ended_at="2024-01-02")
        data = status.to_dict()

        assert data["id"] == "s-1"
        assert data["file_count"] == 10
        assert data["ended_at"] == "2024-01-02"


class TestSlskdSearchFile:
    def test_is_music_file_flac(self):
        file = _make_search_file(filename="song.flac")

        assert file.is_music_file() is True

    def test_is_music_file_mp3(self):
        file = _make_search_file(filename="song.mp3")

        assert file.is_music_file() is True

    def test_is_music_file_opus(self):
        file = _make_search_file(filename="song.opus")

        assert file.is_music_file() is True

    def test_is_music_file_txt(self):
        file = _make_search_file(filename="readme.txt")

        assert file.is_music_file() is False

    def test_is_lossless_true(self):
        file = _make_search_file(filename="song.FLAC")

        assert file.is_lossless() is True

    def test_is_lossless_false(self):
        file = _make_search_file(filename="song.mp3")

        assert file.is_lossless() is False

    def test_is_available_true(self):
        file = _make_search_file(filename="song.flac")

        assert file.is_available() is True

    def test_is_available_false_locked(self):
        file = _make_search_file(is_locked=True)

        assert file.is_available() is False

    def test_is_available_false_not_music(self):
        file = _make_search_file(filename="readme.txt")

        assert file.is_available() is False

    def test_is_matching_track_name_in_filename(self):
        file = _make_search_file(filename="artist - hello world.flac", length=200)
        assert (
            file.is_matching(
                artist_name="Some Artist", track_name="hello world", duration=200
            )
            is True
        )

    def test_is_matching_artist_name_in_filename(self):
        file = _make_search_file(filename="john doe - song.flac", length=200)

        assert (
            file.is_matching(artist_name="john doe", track_name="other", duration=200)
            is True
        )

    def test_is_matching_duration_mismatch(self):
        file = _make_search_file(filename="hello world.flac", length=300)

        assert (
            file.is_matching(
                artist_name="artist", track_name="hello world", duration=200
            )
            is False
        )

    def test_is_matching_no_duration_check_when_zero(self):
        file = _make_search_file(filename="hello world.flac", length=300)

        assert (
            file.is_matching(artist_name="artist", track_name="hello world", duration=0)
            is True
        )

    def test_to_dict(self):
        file = _make_search_file(
            filename="song.flac", length=200, sample_rate=44100, bit_depth=16
        )
        data = file.to_dict()

        assert data["filename"] == "song.flac"
        assert data["sample_rate"] == 44100

    def test_lt_by_bit_depth(self):
        file_a = _make_search_file(filename="a.flac", bit_depth=16)
        file_b = _make_search_file(filename="b.flac", bit_depth=24)

        assert file_a < file_b


class TestSlskdTrackCandidate:
    def test_to_dict(self):
        file = _make_search_file(filename="song.flac")
        candidate = SlskdTrackCandidate(username="user1", file=file)
        data = candidate.to_dict()
        file_data = data["file"]

        assert data["username"] == "user1"
        assert isinstance(file_data, dict)
        assert file_data["filename"] == "song.flac"


class TestSlskdDownloadFile:
    def test_is_downloaded_by_state(self):
        file = _make_download_file()

        assert file.is_downloaded() is True

    def test_is_downloaded_by_percent(self):
        file = _make_download_file(state="Downloading")

        assert file.is_downloaded() is True

    def test_is_not_downloaded(self):
        file = _make_download_file(
            state="Downloading",
            percent_complete=50,
            bytes_transferred=500,
            bytes_remaining=500,
        )
        assert file.is_downloaded() is False

    def test_to_dict(self):
        file = _make_download_file(
            state="Done",
            state_description="ok",
            requested_at="r",
            enqueued_at="e",
            started_at="s",
            ended_at="end",
            average_speed=1.5,
            elapsed_time="10s",
            remaining_time="0s",
            local_path="/path",
        )
        data = file.to_dict()

        assert data["id"] == "d-1"
        assert data["average_speed"] == 1.5


class TestSlskdDownloadDirectory:
    def test_to_dict(self):
        file = _make_download_file(direction="d", filename="f", size=1, state="s")
        directory = SlskdDownloadDirectory(directory="/dl", file_count=1, files=[file])
        result = directory.to_dict()
        files = result["files"]

        assert result["directory"] == "/dl"
        assert isinstance(files, list)
        assert len(files) == 1


class TestSlskdDownloadResult:
    def test_to_dict(self):
        file = _make_download_file(direction="d", filename="f", size=1, state="s")
        directory = SlskdDownloadDirectory(directory="/dl", file_count=1, files=[file])
        result = SlskdDownloadResult(username="user1", directories=[directory])
        data = result.to_dict()
        directories = data["directories"]

        assert data["username"] == "user1"
        assert isinstance(directories, list)
        assert len(directories) == 1
