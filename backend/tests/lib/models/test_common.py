from lib.models.common import (
    ExternalSync,
    ExternalTrack,
    RecommendationTrack,
    ResolvedTrack,
    SyncDiff,
)


def _make_external_track(**overrides) -> ExternalTrack:
    defaults = {
        "artist_name": "Artist",
        "track_name": "Track",
        "album_name": "Album",
        "year": "2024",
        "duration": 200,
    }
    defaults.update(overrides)
    return ExternalTrack(**defaults)


def _make_external_sync(**overrides) -> ExternalSync:
    defaults = {
        "id": "abc-123",
        "name": "My Playlist",
        "thumbnail_url": "https://example.com/thumb.jpg",
        "total": 50,
    }
    defaults.update(overrides)
    return ExternalSync(**defaults)


def _make_recommendation_track(**overrides) -> RecommendationTrack:
    defaults = {
        "artist_name": "Artist",
        "track_name": "Track",
        "musicbrainz_id": "mbid-1",
        "album_name": "Album",
        "year": "2024",
        "duration": 200,
        "playcount": 1000,
        "similarity_score": 0.85,
    }
    defaults.update(overrides)
    return RecommendationTrack(**defaults)


class TestExternalTrack:
    def test_to_dict(self):
        track = _make_external_track()
        d = track.to_dict()
        assert d == {
            "artist_name": "Artist",
            "track_name": "Track",
            "album_name": "Album",
            "year": "2024",
            "duration": 200,
        }


class TestExternalSync:
    def test_to_dict(self):
        sync = _make_external_sync()
        d = sync.to_dict()
        assert d == {
            "id": "abc-123",
            "name": "My Playlist",
            "thumbnail_url": "https://example.com/thumb.jpg",
            "total": 50,
        }


class TestResolvedTrack:
    def test_defaults(self):
        external = _make_external_track()
        resolved = ResolvedTrack(track=external)

        assert resolved.provider_track_id is None
        assert resolved.display_name == ""

    def test_with_values(self):
        external = _make_external_track()
        resolved = ResolvedTrack(
            track=external, provider_track_id="id-1", display_name="Display"
        )

        assert resolved.provider_track_id == "id-1"
        assert resolved.display_name == "Display"


class TestSyncDiff:
    def test_defaults(self):
        diff = SyncDiff()

        assert diff.added == []
        assert diff.removed == []
        assert diff.unchanged == []


class TestRecommendationTrack:
    def test_equality(self):
        a = _make_recommendation_track()
        b = _make_recommendation_track()

        assert a == b

    def test_equality_different_non_key_fields(self):
        a = _make_recommendation_track(playcount=100)
        b = _make_recommendation_track(playcount=200)

        assert a == b

    def test_not_equal_different_artist(self):
        a = _make_recommendation_track(artist_name="A")
        b = _make_recommendation_track(artist_name="B")

        assert a != b

    def test_not_equal_different_track(self):
        a = _make_recommendation_track(track_name="A")
        b = _make_recommendation_track(track_name="B")

        assert a != b

    def test_not_equal_different_mbid(self):
        a = _make_recommendation_track(musicbrainz_id="id-1")
        b = _make_recommendation_track(musicbrainz_id="id-2")

        assert a != b

    def test_not_equal_to_non_track(self):
        a = _make_recommendation_track()

        assert a != "not a track"

    def test_hash_same(self):
        a = _make_recommendation_track()
        b = _make_recommendation_track()

        assert hash(a) == hash(b)

    def test_hash_different(self):
        a = _make_recommendation_track(musicbrainz_id="id-1")
        b = _make_recommendation_track(musicbrainz_id="id-2")

        assert hash(a) != hash(b)

    def test_usable_in_set(self):
        a = _make_recommendation_track()
        b = _make_recommendation_track()

        assert len({a, b}) == 1

    def test_to_external_track(self):
        track = _make_recommendation_track()
        external = track.to_external_track()

        assert isinstance(external, ExternalTrack)
        assert external.artist_name == "Artist"
        assert external.track_name == "Track"
        assert external.album_name == "Album"
        assert external.year == "2024"
        assert external.duration == 200
