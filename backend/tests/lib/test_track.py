from lib.models.common import ExternalTrack, ResolvedTrack
from lib.models.provider import ProviderTrack
from lib.track import (
    _score_track,
    _similarity_score,
    normalize,
    reconcile_after_download,
)


def _make_track(
    track_name="Test Track",
    album_name="Test Album",
    artists=None,
    year="2024",
    duration_ticks=3000000000,  # NOTE: 300 seconds
) -> ProviderTrack:
    return ProviderTrack(
        id="track-1",
        track_name=track_name,
        album_name=album_name,
        album_id="album-1",
        musicbrainz_id="",
        artists=artists or ["Test Artist"],
        duration_ticks=duration_ticks,
        year=year,
    )


class TestNormalize:
    def test_casefold(self):
        assert normalize("Hello World") == normalize("hello world")

    def test_strips_whitespace(self):
        assert normalize("  Hello  ") == normalize("Hello")

    def test_empty_string(self):
        assert normalize("") == ""

    def test_unicode_casefold(self):
        assert normalize("CAFÉ") == normalize("café")

    def test_removes_special_characters(self):
        assert normalize("hello! @world#") == "helloworld"

    def test_removes_internal_spaces(self):
        assert normalize("hello world") == "helloworld"


class TestSimilarityScore:
    def test_identical_strings(self):
        assert _similarity_score("Test Track", "Test Track") == 1.0

    def test_identical_after_normalization(self):
        assert _similarity_score("Test Track!", "testtrack") == 1.0

    def test_similar_strings_high_score(self):
        assert _similarity_score("Test Track", "Test Track (Remastered)") > 0.5

    def test_different_strings_low_score(self):
        assert _similarity_score("Apple", "Zebra") < 0.5

    def test_empty_strings(self):
        assert _similarity_score("", "") == 1.0


class TestScoreTrack:
    def test_perfect_match(self):
        track = _make_track()
        score = _score_track(
            track,
            artist_name="Test Artist",
            track_name="Test Track",
            album_name="Test Album",
            year="2024",
            duration=300,
        )

        assert score == 1.0

    def test_missing_album_lowers_score(self):
        track = _make_track()
        score = _score_track(
            track,
            artist_name="Test Artist",
            track_name="Test Track",
            album_name="",
            year="2024",
            duration=300,
        )

        assert 0 < score < 1.0
        assert score < _score_track(
            track,
            artist_name="Test Artist",
            track_name="Test Track",
            album_name="Test Album",
            year="2024",
            duration=300,
        )

    def test_missing_album_on_track_lowers_score(self):
        track = _make_track(album_name="")
        score = _score_track(
            track,
            artist_name="Test Artist",
            track_name="Test Track",
            album_name="Test Album",
            year="2024",
            duration=300,
        )

        assert 0 < score < 1.0

    def test_wrong_artist_lowers_score(self):
        track = _make_track(artists=["Different Artist"])
        score = _score_track(
            track,
            artist_name="Test Artist",
            track_name="Test Track",
            album_name="Test Album",
            year="2024",
            duration=300,
        )

        assert 0 < score < 1.0

    def test_wrong_year_scores_zero(self):
        track = _make_track(year="1990")
        score = _score_track(
            track,
            artist_name="Test Artist",
            track_name="Test Track",
            album_name="Test Album",
            year="2024",
            duration=300,
        )

        assert score < _score_track(
            _make_track(),
            artist_name="Test Artist",
            track_name="Test Track",
            album_name="Test Album",
            year="2024",
            duration=300,
        )

    def test_duration_mismatch_gives_zero_duration_score(self):
        track = _make_track(duration_ticks=6000000000)
        score = _score_track(
            track,
            artist_name="Test Artist",
            track_name="Test Track",
            album_name="Test Album",
            year="2024",
            duration=300,
        )

        assert score == 0.85
        assert score < _score_track(
            _make_track(),
            artist_name="Test Artist",
            track_name="Test Track",
            album_name="Test Album",
            year="2024",
            duration=300,
        )

    def test_close_duration_still_scores(self):
        track = _make_track(duration_ticks=2900000000)
        score = _score_track(
            track,
            artist_name="Test Artist",
            track_name="Test Track",
            album_name="Test Album",
            year="2024",
            duration=300,
        )

        assert score > 0.85
        assert score < 1.0

    def test_zero_duration_skips_duration_score(self):
        track = _make_track()
        score = _score_track(
            track,
            artist_name="Test Artist",
            track_name="Test Track",
            album_name="Test Album",
            year="2024",
            duration=0,
        )

        assert score == 0.85


def _make_external_track(artist_name: str, track_name: str) -> ExternalTrack:
    return ExternalTrack(
        artist_name=artist_name,
        track_name=track_name,
        album_name="",
        year="2024",
        duration=300,
    )


def _make_resolved_track(artist_name: str, track_name: str) -> ResolvedTrack:
    track = _make_external_track(artist_name, track_name)
    return ResolvedTrack(
        track=track,
        provider_track_id=f"provider-{track_name}",
        display_name=f"{artist_name} - {track_name}",
    )


def _get_key(track: ResolvedTrack) -> tuple[str, str]:
    return (track.track.artist_name, track.track.track_name)


class TestReconcileAfterDownload:
    def test_tracks_found_after_download_move_from_missing_to_found(self):
        found = [_make_resolved_track("Artist A", "Already Found")]
        missing = [
            _make_resolved_track("Artist A", "Now Found"),
            _make_resolved_track("Artist A", "Still Missing"),
        ]
        found_after_download = [_make_resolved_track("Artist A", "Now Found")]
        missing_after_download = [_make_external_track("Artist A", "Still Missing")]
        missing_after_scan = []

        updated_found, updated_missing = reconcile_after_download(
            found,
            found_after_download,
            missing,
            missing_after_download,
            missing_after_scan,
            _get_key,
        )

        assert [t.track.track_name for t in updated_found] == [
            "Already Found",
            "Now Found",
        ]
        assert [t.track.track_name for t in updated_missing] == ["Still Missing"]

    def test_tracks_still_missing_stay_in_missing(self):
        missing = [
            _make_resolved_track("Artist A", "Song 1"),
            _make_resolved_track("Artist A", "Song 2"),
        ]
        missing_after_download = [
            _make_external_track("Artist A", "Song 1"),
            _make_external_track("Artist A", "Song 2"),
        ]

        updated_found, updated_missing = reconcile_after_download(
            [],
            [],
            missing,
            missing_after_download,
            [],
            _get_key,
        )

        assert updated_found == []
        assert {t.track.track_name for t in updated_missing} == {"Song 1", "Song 2"}

    def test_tracks_not_in_original_missing_list_are_ignored(self):
        missing = [_make_resolved_track("Artist A", "Original Missing")]
        found_after_download = [_make_resolved_track("Artist A", "Unknown Found")]
        missing_after_download = [_make_external_track("Artist A", "Unknown Missing")]
        missing_after_scan = [_make_resolved_track("Artist A", "Unknown Scanned")]

        updated_found, updated_missing = reconcile_after_download(
            [],
            found_after_download,
            missing,
            missing_after_download,
            missing_after_scan,
            _get_key,
        )

        assert updated_found == []
        assert updated_missing == []

    def test_missing_tracks_after_scan_are_included(self):
        missing = [_make_resolved_track("Artist A", "Song 1")]
        missing_after_scan = [_make_resolved_track("Artist A", "Song 1")]

        updated_found, updated_missing = reconcile_after_download(
            [],
            [],
            missing,
            [],
            missing_after_scan,
            _get_key,
        )

        assert updated_found == []
        assert [t.track.track_name for t in updated_missing] == ["Song 1"]

    def test_preserves_existing_found_tracks(self):
        found = [_make_resolved_track("Artist A", "Existing")]

        updated_found, updated_missing = reconcile_after_download(
            found,
            [],
            [],
            [],
            [],
            _get_key,
        )

        assert updated_found == found
        assert updated_missing == []

    def test_empty_inputs_return_empty_outputs(self):
        updated_found, updated_missing = reconcile_after_download(
            [], [], [], [], [], _get_key
        )

        assert updated_found == []
        assert updated_missing == []

    def test_matches_from_after_download_and_after_scan_are_appended(self):
        missing = [_make_resolved_track("Artist A", "Song 1")]
        missing_after_download = [_make_external_track("Artist A", "Song 1")]
        missing_after_scan = [_make_resolved_track("Artist A", "Song 1")]

        updated_found, updated_missing = reconcile_after_download(
            [],
            [],
            missing,
            missing_after_download,
            missing_after_scan,
            _get_key,
        )

        assert updated_found == []
        assert [t.track.track_name for t in updated_missing] == ["Song 1", "Song 1"]

