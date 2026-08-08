from pathlib import Path

from lib.models.slskd import (
    SlskdSearchFile,
    SlskdSearchResult,
    SlskdTrackCandidate,
)
from lib.slskd import _cleanup_empty_dirs, _get_ranked_candidates


def _make_search_file(
    filename="/music/Artist/Album/Track.flac",
    size=10000000,
    is_locked=False,
    length=210,
    sample_rate=44100,
    bit_depth=16,
) -> SlskdSearchFile:
    return SlskdSearchFile(
        filename=filename,
        size=size,
        is_locked=is_locked,
        length=length,
        sample_rate=sample_rate,
        bit_depth=bit_depth,
    )


def _make_search_result(
    username="user1",
    files=None,
    has_free_upload_slot=True,
    locked_file_count=0,
    queue_length=0,
    token=1,
    upload_speed=1000000,
) -> SlskdSearchResult:
    return SlskdSearchResult(
        username=username,
        files=files or [],
        has_free_upload_slot=has_free_upload_slot,
        locked_file_count=locked_file_count,
        queue_length=queue_length,
        token=token,
        upload_speed=upload_speed,
    )


class TestGetRankedCandidates:
    def test_sorted_by_bit_depth_then_sample_rate(self):
        entries = [
            _make_search_result(
                files=[_make_search_file(bit_depth=16, sample_rate=44100)]
            ),
            _make_search_result(
                files=[_make_search_file(bit_depth=24, sample_rate=44100)]
            ),
            _make_search_result(
                files=[_make_search_file(bit_depth=24, sample_rate=96000)]
            ),
            _make_search_result(
                files=[_make_search_file(bit_depth=16, sample_rate=192000)]
            ),
        ]
        candidates = _get_ranked_candidates(
            entries=entries,
            artist_name="Artist",
            track_name="Track",
            duration=0,
        )

        assert [
            (candidate.file.bit_depth, candidate.file.sample_rate)
            for candidate in candidates
        ] == [
            (24, 96000),
            (24, 44100),
            (16, 192000),
            (16, 44100),
        ]

    def test_returns_candidate_objects(self):
        entries = [_make_search_result()]
        candidates = _get_ranked_candidates(
            entries=entries,
            artist_name="Artist",
            track_name="Track",
            duration=0,
        )

        assert all(
            isinstance(candidate, SlskdTrackCandidate) for candidate in candidates
        )

    def test_skips_entries_without_free_upload_slot(self):
        entries = [
            _make_search_result(has_free_upload_slot=False),
            _make_search_result(username="user2", files=[_make_search_file()]),
        ]
        candidates = _get_ranked_candidates(
            entries=entries,
            artist_name="Artist",
            track_name="Track",
            duration=0,
        )

        assert len(candidates) == 1
        assert candidates[0].username == "user2"

    def test_skips_locked_files(self):
        entry = _make_search_result(
            files=[
                _make_search_file(is_locked=True),
                _make_search_file(),
            ]
        )

        candidates = _get_ranked_candidates(
            entries=[entry],
            artist_name="Artist",
            track_name="Track",
            duration=0,
        )

        assert len(candidates) == 1
        assert candidates[0].file.is_locked is False

    def test_skips_non_music_files(self):
        entry = _make_search_result(
            files=[
                _make_search_file(filename="/music/Artist/Album/Cover.jpg"),
                _make_search_file(),
            ]
        )
        candidates = _get_ranked_candidates(
            entries=[entry],
            artist_name="Artist",
            track_name="Track",
            duration=0,
        )

        assert len(candidates) == 1
        assert candidates[0].file.filename.endswith(".flac")

    def test_lossless_only_skips_non_lossless_files(self):
        entry = _make_search_result(
            files=[
                _make_search_file(filename="/music/Artist/Album/Track.mp3"),
                _make_search_file(),
            ]
        )

        candidates = _get_ranked_candidates(
            entries=[entry],
            artist_name="Artist",
            track_name="Track",
            duration=0,
            lossless_only=True,
        )

        assert len(candidates) == 1
        assert candidates[0].file.filename.endswith(".flac")

    def test_without_lossless_only_keeps_non_lossless_files(self):
        entry = _make_search_result(
            files=[
                _make_search_file(filename="/music/Artist/Album/Track.mp3"),
                _make_search_file(),
            ]
        )
        candidates = _get_ranked_candidates(
            entries=[entry],
            artist_name="Artist",
            track_name="Track",
            duration=0,
            lossless_only=False,
        )

        assert len(candidates) == 2

    def test_skips_files_that_do_not_match_artist_or_track(self):
        entry = _make_search_result(
            files=[
                _make_search_file(filename="/music/Other/Album/OtherName.flac"),
                _make_search_file(),
            ]
        )

        candidates = _get_ranked_candidates(
            entries=[entry],
            artist_name="Artist",
            track_name="Track",
            duration=0,
        )

        assert len(candidates) == 1
        assert candidates[0].file.filename.endswith("Track.flac")

    def test_skips_files_with_duration_mismatch(self):
        entry = _make_search_result(
            files=[
                _make_search_file(length=210),
                _make_search_file(
                    filename="/music/Artist/Album/Other.flac", length=100
                ),
            ]
        )
        candidates = _get_ranked_candidates(
            entries=[entry],
            artist_name="Artist",
            track_name="Track",
            duration=200,
        )

        assert len(candidates) == 1
        assert candidates[0].file.filename.endswith("Track.flac")

    def test_returns_empty_list_when_no_matches(self):
        candidates = _get_ranked_candidates(
            entries=[],
            artist_name="Artist",
            track_name="Track",
            duration=0,
        )

        assert candidates == []

    def test_returns_empty_list_when_all_filtered_out(self):
        entry = _make_search_result(has_free_upload_slot=False)
        candidates = _get_ranked_candidates(
            entries=[entry],
            artist_name="Artist",
            track_name="Track",
            duration=0,
        )
        assert candidates == []


class TestCleanupEmptyDirs:
    def test_removes_empty_directories_between_src_and_dest(self, tmp_path: Path):
        src = tmp_path / "a" / "b" / "c"
        src.mkdir(parents=True)

        _cleanup_empty_dirs(src=src, dest=tmp_path)

        assert not src.exists()
        assert not (tmp_path / "a").exists()
        assert tmp_path.exists()

    def test_stops_at_non_empty_directory(self, tmp_path: Path):
        src = tmp_path / "a" / "b"
        src.mkdir(parents=True)

        keep = tmp_path / "a" / "keep.txt"
        keep.write_text("x")

        _cleanup_empty_dirs(src=src, dest=tmp_path)

        assert not src.exists()
        assert (tmp_path / "a").exists()
        assert keep.read_text() == "x"

    def test_stops_at_dest_directory(self, tmp_path: Path):
        src = tmp_path / "a" / "b"
        src.mkdir(parents=True)

        _cleanup_empty_dirs(src=src, dest=tmp_path / "a")

        assert (tmp_path / "a").exists()
        assert not (tmp_path / "a" / "b").exists()

    def test_src_equals_dest_is_noop(self, tmp_path: Path):
        target = tmp_path / "dir"
        target.mkdir()

        _cleanup_empty_dirs(src=target, dest=target)

        assert target.exists()

