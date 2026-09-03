import re

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlmodel import Session, select

from db.library import (
    PRESERVED_COLUMNS,
    TRACK_COLUMNS,
    count_duplicate_tracks,
    delete_tracks_by_paths,
    duplicate_groups,
    get_empty_folders,
    get_track_by_path,
    get_track_fingerprints,
    query_tracks,
    replace_empty_folders,
    summarize_library,
    upsert_tracks,
)
from db.models.library import LibraryTrack


def _make_track(path: str = "Artist/Album/Track.flac", **overrides) -> LibraryTrack:
    defaults = {
        "path": path,
        "filename": path.rsplit("/", 1)[-1],
        "directory": path.rsplit("/", 1)[0] if "/" in path else "",
        "format": "flac",
        "size": 1024,
        "duration": 200,
        "mtime": 1.0,
        "title": "Blinding Lights",
        "artist": "The Weeknd",
        "album": "After Hours",
        "date": "2020",
        "genres": ["synth-pop"],
        "musicbrainz_id": "9b1a2b3c",
        "has_lyrics": True,
        "is_synced_lyrics": False,
    }
    defaults.update(overrides)

    return LibraryTrack(**defaults)


class TestUpsertTracks:
    def test_inserts_new_tracks(self, session: Session):
        upsert_tracks(session, [_make_track()])

        assert get_track_by_path(session, "Artist/Album/Track.flac") is not None

    def test_updates_rather_than_duplicating_a_known_path(self, session: Session):
        upsert_tracks(session, [_make_track()])
        upsert_tracks(session, [_make_track(title="Renamed", mtime=99.0)])

        track = get_track_by_path(session, "Artist/Album/Track.flac")

        assert track is not None
        assert track.title == "Renamed"
        assert track.mtime == 99.0
        assert summarize_library(session)["total"] == 1

    def test_accepts_an_empty_batch(self, session: Session):
        upsert_tracks(session, [])

        assert summarize_library(session)["total"] == 0

    def test_only_row_identity_and_db_timestamps_are_preserved(self):
        """TRACK_COLUMNS is everything else, so a new model column is updated by default.

        Adding a name here silently stops that column being refreshed on rows that
        already exist, which shows up as stale data rather than as a failure.
        """

        assert PRESERVED_COLUMNS == {"id", "path", "created_at", "updated_at"}

    def test_refreshes_every_column_except_the_preserved_ones(self, session: Session):
        upsert_tracks(session, [_make_track()])
        original = get_track_by_path(session, "Artist/Album/Track.flac")
        assert original is not None

        before = {column: getattr(original, column) for column in TRACK_COLUMNS}
        original_id = original.id
        created_at = original.created_at

        upsert_tracks(
            session,
            [
                _make_track(
                    filename="Renamed.flac",
                    directory="Other/Place",
                    format="opus",
                    size=99,
                    duration=1,
                    mtime=42.0,
                    title="Renamed",
                    artist="Someone Else",
                    album="Elsewhere",
                    date="1999",
                    genres=["rock"],
                    musicbrainz_id="zzz",
                    has_lyrics=False,
                    is_synced_lyrics=True,
                )
            ],
        )

        refreshed = get_track_by_path(session, "Artist/Album/Track.flac")
        assert refreshed is not None

        for column in TRACK_COLUMNS:
            assert getattr(refreshed, column) != before[column], column

        assert refreshed.id == original_id
        assert refreshed.created_at == created_at


class TestGetTrackFingerprints:
    def test_maps_every_path_to_its_mtime_and_size(self, session: Session):
        upsert_tracks(
            session,
            [
                _make_track(path="A.flac", mtime=1.5, size=10),
                _make_track(path="B.flac", mtime=2.5, size=20),
            ],
        )

        assert get_track_fingerprints(session) == {
            "A.flac": (1.5, 10),
            "B.flac": (2.5, 20),
        }


class TestDeleteTracksByPaths:
    def test_removes_the_named_paths(self, session: Session):
        upsert_tracks(session, [_make_track(path="A.flac"), _make_track(path="B.flac")])

        assert delete_tracks_by_paths(session, ["A.flac"]) == 1
        assert sorted(get_track_fingerprints(session)) == ["B.flac"]

    def test_accepts_an_empty_list(self, session: Session):
        assert delete_tracks_by_paths(session, []) == 0


class TestQueryTracks:
    def test_matches_free_text_against_tags_and_filenames(self, session: Session):
        upsert_tracks(
            session,
            [
                _make_track(),
                _make_track(path="Other/Other/Other.flac", title="Other"),
            ],
        )

        _, matched = query_tracks(session, query="weeknd")
        assert matched == 2

        _, matched = query_tracks(session, query="blinding")
        assert matched == 1

    def test_matches_regardless_of_case(self, session: Session):
        upsert_tracks(session, [_make_track()])

        _, matched = query_tracks(session, query="WEEKND")

        assert matched == 1

    def test_matches_composed_and_decomposed_spellings_alike(self, session: Session):
        """A name stored NFC must still be found when the query arrives NFD."""

        upsert_tracks(session, [_make_track(path="IU/Track.flac", title="아이")])

        _, matched = query_tracks(session, query="아이")

        assert matched == 1

    def test_filters_by_format(self, session: Session):
        upsert_tracks(
            session,
            [_make_track(), _make_track(path="A/B/C.mp3", format="mp3")],
        )

        tracks, matched = query_tracks(session, file_format="mp3")

        assert [track.format for track in tracks] == ["mp3"]
        assert matched == 1

    def test_filters_by_missing_lyrics(self, session: Session):
        upsert_tracks(
            session,
            [_make_track(), _make_track(path="A/B/C.flac", has_lyrics=False)],
        )

        tracks, _ = query_tracks(session, missing="lyrics")

        assert [track.path for track in tracks] == ["A/B/C.flac"]

    def test_filters_by_missing_musicbrainz_id(self, session: Session):
        upsert_tracks(
            session,
            [_make_track(), _make_track(path="A/B/C.flac", musicbrainz_id="")],
        )

        tracks, _ = query_tracks(session, missing="musicbrainz_id")

        assert [track.path for track in tracks] == ["A/B/C.flac"]

    def test_filters_by_any_missing_tag(self, session: Session):
        upsert_tracks(
            session, [_make_track(), _make_track(path="A/B/C.flac", album="")]
        )

        tracks, _ = query_tracks(session, missing="any")

        assert [track.path for track in tracks] == ["A/B/C.flac"]

    def test_catches_a_file_missing_only_its_genres(self, session: Session):
        """Genres live in a JSON column, so emptiness is checked as text."""

        upsert_tracks(
            session, [_make_track(), _make_track(path="A/B/C.flac", genres=[])]
        )

        tracks, _ = query_tracks(session, missing="any")

        assert [track.path for track in tracks] == ["A/B/C.flac"]

    def test_keeps_a_fully_tagged_file_out_of_the_missing_filter(
        self, session: Session
    ):
        upsert_tracks(session, [_make_track()])

        _, matched = query_tracks(session, missing="any")

        assert matched == 0

    def test_pages_without_changing_the_match_count(self, session: Session):
        upsert_tracks(
            session, [_make_track(path=f"Artist/{index}.flac") for index in range(5)]
        )

        tracks, matched = query_tracks(session, limit=2, offset=2)

        assert matched == 5
        assert len(tracks) == 2

    def test_orders_by_path_case_insensitively(self, session: Session):
        upsert_tracks(
            session,
            [
                _make_track(path="b.flac"),
                _make_track(path="A.flac"),
                _make_track(path="c.flac"),
            ],
        )

        tracks, _ = query_tracks(session)

        assert [track.path for track in tracks] == ["A.flac", "b.flac", "c.flac"]


class TestDuplicateGroupsSql:
    def test_groups_by_the_very_expression_it_selects(self):
        statement = select(sa.func.count()).select_from(duplicate_groups())
        sql = str(statement.compile(dialect=postgresql.dialect()))

        cases = re.findall(r"CASE WHEN.*?END", sql, re.DOTALL)

        assert len(cases) == 2, "expected the key in both the SELECT and GROUP BY"
        assert cases[0] == cases[1], "GROUP BY must reuse the selected expression"


class TestCountDuplicateTracks:
    def test_counts_a_track_held_in_two_formats_once(self, session: Session):
        upsert_tracks(
            session,
            [
                _make_track(path="Artist/Album/Track.flac"),
                _make_track(path="Artist/Album/Track.opus", format="opus"),
            ],
        )

        assert count_duplicate_tracks(session) == 1

    def test_counts_each_duplicated_track_once_however_many_copies(
        self, session: Session
    ):
        upsert_tracks(
            session,
            [
                _make_track(path="A/B/C.flac"),
                _make_track(path="A/B/C.mp3", format="mp3"),
                _make_track(path="A/B/C.opus", format="opus"),
            ],
        )

        assert count_duplicate_tracks(session) == 1

    def test_keeps_distinct_tracks_apart(self, session: Session):
        upsert_tracks(
            session,
            [
                _make_track(path="A/B/C.flac"),
                _make_track(path="D/E/F.flac", artist="Someone Else"),
            ],
        )

        assert count_duplicate_tracks(session) == 0

    def test_matches_the_same_recording_across_folders(self, session: Session):
        upsert_tracks(
            session,
            [
                _make_track(path="Artist/Album/Track.flac"),
                _make_track(
                    path="Artist/Greatest Hits/Track.opus",
                    directory="Artist/Greatest Hits",
                    format="opus",
                ),
            ],
        )

        assert count_duplicate_tracks(session) == 1

    def test_ignores_case_when_matching(self, session: Session):
        upsert_tracks(
            session,
            [
                _make_track(path="A/B/C.flac", title="Blinding Lights"),
                _make_track(path="A/B/D.opus", format="opus", title="BLINDING LIGHTS"),
            ],
        )

        assert count_duplicate_tracks(session) == 1

    def test_falls_back_to_the_folder_and_file_name_when_untagged(
        self, session: Session
    ):
        upsert_tracks(
            session,
            [
                _make_track(
                    path="A/Album One/01.flac",
                    directory="A/Album One",
                    filename="01.flac",
                    title="",
                    artist="",
                ),
                _make_track(
                    path="A/Album Two/01.flac",
                    directory="A/Album Two",
                    filename="01.flac",
                    title="",
                    artist="",
                ),
            ],
        )

        assert count_duplicate_tracks(session) == 0

    def test_matches_untagged_files_sharing_a_folder_and_name(self, session: Session):
        upsert_tracks(
            session,
            [
                _make_track(
                    path="A/Album One/01.flac",
                    directory="A/Album One",
                    filename="01.flac",
                    title="",
                    artist="",
                ),
                _make_track(
                    path="A/Album One/01.opus",
                    directory="A/Album One",
                    filename="01.opus",
                    format="opus",
                    title="",
                    artist="",
                ),
            ],
        )

        assert count_duplicate_tracks(session) == 1

    def test_separates_the_two_halves_of_the_key(self, session: Session):
        """Without a separator, artist "AB" + title "C" collides with "A" + "BC"."""

        upsert_tracks(
            session,
            [
                _make_track(path="A/B/C.flac", artist="AB", title="C"),
                _make_track(path="A/B/D.flac", artist="A", title="BC"),
            ],
        )

        assert count_duplicate_tracks(session) == 0


class TestEmptyFolders:
    def test_stores_the_folders_the_sweep_found(self, session: Session):
        replace_empty_folders(session, ["Abandoned", "Artwork Only"])

        assert [folder.path for folder in get_empty_folders(session)] == [
            "Abandoned",
            "Artwork Only",
        ]

    def test_replaces_rather_than_accumulating(self, session: Session):
        replace_empty_folders(session, ["Abandoned", "Artwork Only"])
        replace_empty_folders(session, ["Abandoned"])

        assert [folder.path for folder in get_empty_folders(session)] == ["Abandoned"]

    def test_clears_the_table_when_nothing_is_empty(self, session: Session):
        replace_empty_folders(session, ["Abandoned"])
        replace_empty_folders(session, [])

        assert get_empty_folders(session) == []


class TestSummarizeLibrary:
    def test_counts_the_gaps_worth_acting_on(self, session: Session):
        upsert_tracks(
            session,
            [
                _make_track(),
                _make_track(
                    path="A/B/C.mp3", format="mp3", has_lyrics=False, title="C"
                ),
                _make_track(path="A/B/D.flac", musicbrainz_id="", title="D"),
            ],
        )
        replace_empty_folders(session, ["Dead One", "Dead Two"])

        assert summarize_library(session) == {
            "total": 3,
            "missing_lyrics": 1,
            "missing_musicbrainz_id": 1,
            "lossless": 2,
            "duplicates": 0,
            "empty_directories": 2,
        }

    def test_reports_zeroes_for_an_empty_library(self, session: Session):
        assert summarize_library(session) == {
            "total": 0,
            "missing_lyrics": 0,
            "missing_musicbrainz_id": 0,
            "lossless": 0,
            "duplicates": 0,
            "empty_directories": 0,
        }
