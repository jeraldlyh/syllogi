from lib.models.chart import ChartTrendingTrack


def _make_track(**overrides) -> ChartTrendingTrack:
    defaults = {
        "artist_name": "Artist",
        "track_name": "Track",
        "album_name": "Album",
        "duration": 200,
        "listeners": 1000,
        "playcount": 5000,
        "musicbrainz_id": "mbid-123",
        "image_url": "https://example.com/image.jpg",
    }
    defaults.update(overrides)
    return ChartTrendingTrack(**defaults)


class TestChartTrendingTrackEquality:
    def test_equal_same_fields(self):
        a = _make_track()
        b = _make_track()

        assert a == b

    def test_equal_different_non_key_fields(self):
        a = _make_track(duration=200)
        b = _make_track(duration=300)

        assert a == b

    def test_not_equal_different_artist(self):
        a = _make_track(artist_name="Artist A")
        b = _make_track(artist_name="Artist B")

        assert a != b

    def test_not_equal_different_track(self):
        a = _make_track(track_name="Track A")
        b = _make_track(track_name="Track B")

        assert a != b

    def test_not_equal_different_mbid(self):
        a = _make_track(musicbrainz_id="id-1")
        b = _make_track(musicbrainz_id="id-2")

        assert a != b

    def test_not_equal_to_non_track(self):
        a = _make_track()

        assert a != "not a track"


class TestChartTrendingTrackHash:
    def test_same_hash(self):
        a = _make_track()
        b = _make_track()

        assert hash(a) == hash(b)

    def test_usable_in_set(self):
        a = _make_track()
        b = _make_track()

        assert len({a, b}) == 1

    def test_different_hash_different_artist(self):
        a = _make_track(artist_name="A")
        b = _make_track(artist_name="B")

        assert hash(a) != hash(b)


class TestChartTrendingTrackToDict:
    def test_returns_all_fields(self):
        track = _make_track()
        data = track.to_dict()

        assert data["artist_name"] == "Artist"
        assert data["track_name"] == "Track"
        assert data["album_name"] == "Album"
        assert data["duration"] == 200
        assert data["listeners"] == 1000
        assert data["playcount"] == 5000
        assert data["musicbrainz_id"] == "mbid-123"
        assert data["image_url"] == "https://example.com/image.jpg"

    def test_dict_values_are_correct_types(self):
        track = _make_track()
        data = track.to_dict()

        assert isinstance(data["artist_name"], str)
        assert isinstance(data["duration"], int)
        assert isinstance(data["listeners"], int)
