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
