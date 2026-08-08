from lib.youtube import (
    _get_best_entry,
    _is_bad_fallback,
    _is_lyrics_video,
    _score_entry,
)


class TestScoreEntry:
    def test_official_audio_title_scores_high(self):
        entry = {
            "title": "Song Name (Official Audio)",
            "uploader": "",
            "view_count": 0,
        }

        assert _score_entry(entry) >= 0.5

    def test_audio_title_scores(self):
        entry = {"title": "Song Name Audio", "uploader": "", "view_count": 0}

        assert _score_entry(entry) >= 0.3

    def test_official_uploader_adds_score(self):
        entry = {"title": "", "uploader": "Artist Official", "view_count": 0}

        assert _score_entry(entry) == 0.2

    def test_view_count_contributes_one_point_per_million(self):
        entry = {"title": "", "uploader": "", "view_count": 2_000_000}

        assert _score_entry(entry) == 1.0

    def test_view_count_contribution_capped_at_one_million(self):
        entry = {"title": "", "uploader": "", "view_count": 1_500_000}

        assert _score_entry(entry) == 1.0

    def test_view_count_under_one_million_contributes_nothing(self):
        entry = {"title": "", "uploader": "", "view_count": 999_999}

        assert _score_entry(entry) == 0.0

    def test_empty_and_missing_fields_score_zero(self):
        assert _score_entry({}) == 0.0
        assert _score_entry({"title": None, "uploader": None, "view_count": None}) == 0.0


class TestIsLyricsVideo:
    def test_lyrics_in_title(self):
        assert _is_lyrics_video({"title": "Song Name (Lyrics)"})

    def test_lyric_video_in_title(self):
        assert _is_lyrics_video({"title": "Song Name Lyric Video"})

    def test_official_audio_is_not_lyrics_video(self):
        assert not _is_lyrics_video({"title": "Song Name Official Audio"})

    def test_missing_title(self):
        assert not _is_lyrics_video({})


class TestIsBadFallback:
    def test_live_in_title(self):
        assert _is_bad_fallback({"title": "Song Name (Live)"})

    def test_official_audio_is_not_bad_fallback(self):
        assert not _is_bad_fallback({"title": "Song Name Official Audio"})

    def test_missing_title(self):
        assert not _is_bad_fallback({})


class TestGetBestEntry:
    def test_prefers_lyrics_video_over_regular(self):
        regular = {"title": "Song Name", "view_count": 100}
        lyrics = {"title": "Song Name (Lyrics)", "view_count": 50}

        assert _get_best_entry([regular, lyrics]) == lyrics

    def test_only_bad_fallback_entries_returns_none(self):
        entries = [{"title": "Song Name (Live)"}]

        assert _get_best_entry(entries) is None

    def test_skips_empty_and_none_entries(self):
        entries = [None, {}, {"title": "Song Name"}]

        assert _get_best_entry(entries) == {"title": "Song Name"}

    def test_skips_live_entries(self):
        regular = {"title": "Song Name"}
        live = {"title": "Song Name", "is_live": True}

        assert _get_best_entry([live, regular]) == regular
        assert _get_best_entry([live]) is None
