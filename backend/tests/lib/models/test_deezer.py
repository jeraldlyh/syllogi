from lib.models.deezer import DeezerTrack


def _make_deezer_track(**overrides) -> DeezerTrack:
    defaults = {
        "title": "Song",
        "album_name": "Album",
        "image_url": "https://example.com/img.jpg",
        "duration": 200,
    }
    defaults.update(overrides)
    return DeezerTrack(**defaults)


class TestDeezerTrack:
    def test_creation(self):
        track = _make_deezer_track()

        assert track.title == "Song"
        assert track.album_name == "Album"
        assert track.image_url == "https://example.com/img.jpg"
        assert track.duration == 200

    def test_optional_image_url(self):
        track = _make_deezer_track(image_url=None)

        assert track.image_url is None
