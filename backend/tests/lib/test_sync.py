from lib.models.common import ExternalTrack, ResolvedTrack
from lib.models.provider import ProviderTrack
from lib.sync import _diff_tracks


def _make_provider_track(id="track-1", track_name="Song", artists=None):
    return ProviderTrack(
        id=id,
        track_name=track_name,
        album_name="",
        album_id="",
        musicbrainz_id="",
        artists=artists or ["Artist"],
        duration_ticks=0,
        year="",
    )


def _make_resolved_track(
    track_name="Song",
    artist_name="Artist",
    provider_track_id: str | None = "track-1",
):
    external = ExternalTrack(
        artist_name=artist_name,
        track_name=track_name,
        album_name="",
        year="",
        duration=0,
    )
    return ResolvedTrack(
        track=external,
        provider_track_id=provider_track_id,
        display_name=f"{artist_name}: {track_name}",
    )


class TestDiffTracks:
    def test_track_in_source_not_in_provider_goes_to_added(self):
        diff = _diff_tracks(
            resolved_tracks=[_make_resolved_track(provider_track_id="track-1")],
            existing_tracks=[],
        )

        assert len(diff.added) == 1
        assert diff.added[0].provider_track_id == "track-1"
        assert diff.removed == []
        assert diff.unchanged == []

    def test_track_in_provider_not_in_source_goes_to_removed(self):
        diff = _diff_tracks(
            resolved_tracks=[],
            existing_tracks=[_make_provider_track(id="track-1")],
        )

        assert len(diff.removed) == 1
        assert diff.removed[0].id == "track-1"
        assert diff.added == []
        assert diff.unchanged == []

    def test_track_in_both_goes_to_unchanged(self):
        diff = _diff_tracks(
            resolved_tracks=[_make_resolved_track(provider_track_id="track-1")],
            existing_tracks=[_make_provider_track(id="track-1")],
        )

        assert len(diff.unchanged) == 1
        assert diff.unchanged[0].provider_track_id == "track-1"
        assert diff.added == []
        assert diff.removed == []

    def test_source_track_without_provider_track_id_is_skipped(self):
        diff = _diff_tracks(
            resolved_tracks=[_make_resolved_track(provider_track_id=None)],
            existing_tracks=[_make_provider_track(id="track-1")],
        )

        assert diff.added == []
        assert diff.unchanged == []
        assert [track.id for track in diff.removed] == ["track-1"]

    def test_empty_inputs_produce_empty_diff(self):
        diff = _diff_tracks(resolved_tracks=[], existing_tracks=[])

        assert diff.added == []
        assert diff.removed == []
        assert diff.unchanged == []

    def test_mixed_scenario(self):
        resolved_tracks = [
            _make_resolved_track(track_name="New Song", provider_track_id="track-2"),
            _make_resolved_track(track_name="Keep Song", provider_track_id="track-1"),
            _make_resolved_track(provider_track_id=None),
        ]
        existing_tracks = [
            _make_provider_track(id="track-1", track_name="Keep Song"),
            _make_provider_track(id="track-3", track_name="Old Song"),
        ]

        diff = _diff_tracks(
            resolved_tracks=resolved_tracks,
            existing_tracks=existing_tracks,
        )

        assert [track.provider_track_id for track in diff.added] == ["track-2"]
        assert [track.id for track in diff.removed] == ["track-3"]
        assert [track.provider_track_id for track in diff.unchanged] == ["track-1"]

