from lib.models.metadata import ArtistInfo
from lib.models.musicbrainz import (
    MusicbrainzArtist,
    MusicbrainzArtistAlias,
    MusicbrainzArtistArea,
    MusicbrainzArtistTag,
)


def _make_artist(**overrides) -> MusicbrainzArtist:
    defaults = {
        "id": "mb-1",
        "type": "Person",
        "type_id": "type-1",
        "score": 100,
        "gender_id": "gender-1",
        "name": "Test Artist",
        "sort_name": "Artist, Test",
        "gender": "Male",
        "country": "US",
        "area": MusicbrainzArtistArea(
            id="area-1",
            type="Country",
            type_id="t-1",
            name="United States",
            sort_name="United States",
            life_span={"ended": None},
        ),
        "begin_area": MusicbrainzArtistArea(
            id="area-2",
            type="City",
            type_id="t-2",
            name="New York",
            sort_name="New York",
            life_span={"ended": None},
        ),
        "ipis": [],
        "isnis": [],
        "life_span": {"begin": "2000", "end": None, "ended": False},
        "aliases": [],
        "tags": [],
    }
    defaults.update(overrides)
    return MusicbrainzArtist(**defaults)


class TestMusicbrainzArtistToArtistInfo:
    def test_basic_conversion(self):
        artist = _make_artist()
        info = artist.to_artist_info()

        assert isinstance(info, ArtistInfo)
        assert info.id == "mb-1"
        assert info.name == "Test Artist"
        assert info.type == "Person"
        assert info.country == "US"
        assert info.gender == "Male"
        assert info.area == "United States"
        assert info.begin_area == "New York"
        assert info.life_span == {"begin": "2000", "end": None, "ended": False}

    def test_tags_converted(self):
        tags = [
            MusicbrainzArtistTag(count=10, name="rock"),
            MusicbrainzArtistTag(count=5, name="pop"),
        ]
        artist = _make_artist(tags=tags)
        info = artist.to_artist_info()

        assert info.tags == ["rock", "pop"]

    def test_aliases_all_when_no_locale(self):
        aliases = [
            MusicbrainzArtistAlias(
                sort_name="A",
                name="Alias1",
                locale="en",
                type="Artist name",
                primary=True,
                begin_date=None,
                end_date=None,
            ),
            MusicbrainzArtistAlias(
                sort_name="B",
                name="Alias2",
                locale="ja",
                type="Artist name",
                primary=False,
                begin_date=None,
                end_date=None,
            ),
        ]
        artist = _make_artist(aliases=aliases)
        info = artist.to_artist_info(locale=None)

        assert len(info.aliases) == 2

    def test_aliases_filtered_by_locale(self):
        aliases = [
            MusicbrainzArtistAlias(
                sort_name="A",
                name="Alias1",
                locale="en",
                type="Artist name",
                primary=True,
                begin_date=None,
                end_date=None,
            ),
            MusicbrainzArtistAlias(
                sort_name="B",
                name="Alias2",
                locale="ja",
                type="Artist name",
                primary=False,
                begin_date=None,
                end_date=None,
            ),
        ]
        artist = _make_artist(aliases=aliases)
        info = artist.to_artist_info(locale="en-US")

        assert info.aliases == ["Alias2"]

    def test_aliases_fallback_when_no_match(self):
        aliases = [
            MusicbrainzArtistAlias(
                sort_name="A",
                name="Alias1",
                locale="en",
                type="Artist name",
                primary=True,
                begin_date=None,
                end_date=None,
            ),
        ]
        artist = _make_artist(aliases=aliases)
        info = artist.to_artist_info(locale="fr-FR")

        assert info.aliases == ["Alias1"]
