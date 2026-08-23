from lib.models.metadata import ArtistTrack


def _make_track(**overrides) -> ArtistTrack:
    defaults = {
        "artist_name": "Artist",
        "track_name": "Track",
        "duration_ms": 200000,
        "disambiguation": "",
        "album_name": "Album",
        "genres": ["rock"],
        "image_url": "https://example.com/image.jpg",
    }
    defaults.update(overrides)

    return ArtistTrack(**defaults)


class TestArtistTrackEquality:
    def test_equal_same_track_name(self):
        a = _make_track(track_name="Song")
        b = _make_track(track_name="Song")

        assert a == b

    def test_equal_case_insensitive(self):
        a = _make_track(track_name="Song")
        b = _make_track(track_name="song")

        assert a == b

    def test_not_equal_different_track(self):
        a = _make_track(track_name="Song A")
        b = _make_track(track_name="Song B")

        assert a != b

    def test_not_equal_to_non_track(self):
        a = _make_track()

        assert a != "not a track"


class TestArtistTrackHash:
    def test_same_hash_same_track(self):
        a = _make_track(track_name="Song")
        b = _make_track(track_name="Song")

        assert hash(a) == hash(b)

    def test_same_hash_case_insensitive(self):
        a = _make_track(track_name="Song")
        b = _make_track(track_name="song")

        assert hash(a) == hash(b)

    def test_usable_in_set(self):
        a = _make_track(track_name="Song")
        b = _make_track(track_name="song")

        assert len({a, b}) == 1


class TestArtistTrackGetDuration:
    def test_returns_seconds(self):
        track = _make_track(duration_ms=125000)

        assert track.get_duration() == 125

    def test_rounds_down(self):
        track = _make_track(duration_ms=125999)

        assert track.get_duration() == 125

    def test_zero_when_none(self):
        track = _make_track(duration_ms=None)

        assert track.get_duration() == 0

    def test_zero_when_zero(self):
        track = _make_track(duration_ms=0)

        assert track.get_duration() == 0


class TestArtistTrackRecordingFields:
    def test_defaults_are_empty(self):
        track = _make_track()

        assert track.id == ""
        assert track.release_date == ""
        assert track.score == 0


class TestArtistTrackGetYear:
    def test_returns_year_from_full_date(self):
        track = _make_track(release_date="2020-03-20")

        assert track.get_year() == "2020"

    def test_returns_year_from_year_month(self):
        track = _make_track(release_date="2020-03")

        assert track.get_year() == "2020"

    def test_returns_year_when_already_a_year(self):
        track = _make_track(release_date="2020")

        assert track.get_year() == "2020"

    def test_empty_when_no_release_date(self):
        track = _make_track()

        assert track.get_year() == ""


class TestArtistTrackToSearchDict:
    def test_maps_track_name_to_title_and_derives_fields(self):
        track = _make_track(
            track_name="Blinding Lights",
            artist_name="The Weeknd",
            album_name="After Hours",
            duration_ms=200040,
            genres=["synth-pop"],
            id="9b1a2b3c-4d5e-6f70-8192-a3b4c5d6e7f8",
            release_date="2020-03-20",
            score=100,
        )

        assert track.to_search_dict() == {
            "id": "9b1a2b3c-4d5e-6f70-8192-a3b4c5d6e7f8",
            "title": "Blinding Lights",
            "artist_name": "The Weeknd",
            "album_name": "After Hours",
            "release_date": "2020-03-20",
            "year": "2020",
            "duration": 200,
            "disambiguation": "",
            "genres": ["synth-pop"],
            "score": 100,
        }
