from unittest.mock import AsyncMock, MagicMock, call

import pytest

from db.models.recommendation import RecommendationStrategy
from lib.models.common import RecommendationTrack
from lib.models.provider import ProviderTrack
from lib.recommendation import get_recommendations


def _make_recommendation_track(
    artist_name="Test Artist",
    track_name="Test Track",
    album_name="Test Album",
    musicbrainz_id="",
    duration=300,
    year="2024",
) -> RecommendationTrack:
    return RecommendationTrack(
        artist_name=artist_name,
        track_name=track_name,
        album_name=album_name,
        musicbrainz_id=musicbrainz_id,
        year=year,
        duration=duration,
        playcount=0,
        similarity_score=1.0,
    )


def _make_recommendation_provider():
    provider = MagicMock()
    provider.get_top_tracks = AsyncMock(return_value=[])
    provider.get_recent_tracks = AsyncMock(return_value=[])
    provider.get_similar_tracks = AsyncMock(return_value=[])

    return provider


def _make_music_provider(provider_tracks=None):
    provider = MagicMock()
    provider.search_track = AsyncMock(return_value=provider_tracks or [])

    return provider


def _make_music_provider_with_tracks(tracks: list[RecommendationTrack]):
    by_track_name = {
        track.track_name: _make_matching_provider_track(track) for track in tracks
    }

    async def search_track(*, artist_name, title, album, year):
        provider_track = by_track_name.get(title)

        return [provider_track] if provider_track else []

    provider = MagicMock()
    provider.search_track = AsyncMock(side_effect=search_track)

    return provider


def _make_matching_provider_track(track: RecommendationTrack) -> ProviderTrack:
    return ProviderTrack(
        id="provider-1",
        track_name=track.track_name,
        album_name=track.album_name,
        album_id="album-1",
        musicbrainz_id="",
        artists=[track.artist_name],
        duration_ticks=track.duration * 10_000_000,
        year=track.year,
    )


class TestStrategies:
    async def test_top_tracks_strategy(self):
        recommendation_provider = _make_recommendation_provider()
        music_provider = _make_music_provider()

        found, missing, provider_tracks = await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.top_tracks,
            num_recommendations=10,
            username="user",
            blend_users=None,
        )

        recommendation_provider.get_top_tracks.assert_awaited_once_with(
            username="user", limit=10
        )
        recommendation_provider.get_recent_tracks.assert_not_awaited()
        recommendation_provider.get_similar_tracks.assert_not_awaited()
        assert found == []
        assert missing == []
        assert provider_tracks == []

    async def test_recent_tracks_strategy(self):
        recommendation_provider = _make_recommendation_provider()
        music_provider = _make_music_provider()

        await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.recent_tracks,
            num_recommendations=10,
            username="user",
            blend_users=None,
        )

        recommendation_provider.get_recent_tracks.assert_awaited_once_with(
            username="user", limit=10
        )
        recommendation_provider.get_top_tracks.assert_not_awaited()

    async def test_mixed_strategy(self):
        recommendation_provider = _make_recommendation_provider()
        music_provider = _make_music_provider()

        await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.mixed,
            num_recommendations=10,
            username="user",
            blend_users=None,
        )

        recommendation_provider.get_recent_tracks.assert_awaited_once_with(
            username="user", limit=5
        )
        recommendation_provider.get_top_tracks.assert_awaited_once_with(
            username="user", limit=5
        )

    async def test_mixed_strategy_splits_rounding(self):
        recommendation_provider = _make_recommendation_provider()
        music_provider = _make_music_provider()

        await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.mixed,
            num_recommendations=7,
            username="user",
            blend_users=None,
        )

        recommendation_provider.get_recent_tracks.assert_awaited_once_with(
            username="user", limit=4
        )
        recommendation_provider.get_top_tracks.assert_awaited_once_with(
            username="user", limit=3
        )

    async def test_blend_strategy(self):
        recommendation_provider = _make_recommendation_provider()
        music_provider = _make_music_provider()
        blend_users = [("alice", "alice-prov"), ("bob", "bob-prov")]

        await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.blend,
            num_recommendations=10,
            username="user",
            blend_users=blend_users,
        )

        assert recommendation_provider.get_recent_tracks.await_args_list == [
            call(username="alice-prov", limit=2),
            call(username="bob-prov", limit=2),
        ]
        assert recommendation_provider.get_top_tracks.await_args_list == [
            call(username="alice-prov", limit=2),
            call(username="bob-prov", limit=2),
        ]

    async def test_blend_strategy_uses_user_mapping(self):
        recommendation_provider = _make_recommendation_provider()
        music_provider = _make_music_provider()

        await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.blend,
            num_recommendations=5,
            username="user",
            blend_users=[("carol_music", "carol_provider")],
        )

        recommendation_provider.get_recent_tracks.assert_awaited_once_with(
            username="carol_provider", limit=2
        )
        recommendation_provider.get_top_tracks.assert_awaited_once_with(
            username="carol_provider", limit=2
        )

    async def test_blend_strategy_raises_without_users(self):
        recommendation_provider = _make_recommendation_provider()
        music_provider = _make_music_provider()

        with pytest.raises(ValueError, match="blend_users required"):
            await get_recommendations(
                recommendation_provider=recommendation_provider,
                music_provider=music_provider,
                strategy=RecommendationStrategy.blend,
                num_recommendations=10,
                username="user",
                blend_users=None,
            )


class TestTrackMatching:
    async def test_finds_and_returns_matching_tracks(self):
        seed_track = _make_recommendation_track(track_name="Seed Track")
        similar_track = _make_recommendation_track()

        recommendation_provider = _make_recommendation_provider()
        recommendation_provider.get_top_tracks.return_value = [seed_track]
        recommendation_provider.get_similar_tracks.return_value = [similar_track]

        provider_track = _make_matching_provider_track(similar_track)
        music_provider = _make_music_provider([provider_track])

        found, missing, provider_tracks = await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.top_tracks,
            num_recommendations=1,
            username="user",
            blend_users=None,
        )

        assert found == [similar_track]
        assert missing == []
        assert provider_tracks == [provider_track]
        recommendation_provider.get_similar_tracks.assert_awaited_once_with(
            artist_name=seed_track.artist_name,
            track_name=seed_track.track_name,
            musicbrainz_id=seed_track.musicbrainz_id,
        )
        music_provider.search_track.assert_awaited_once_with(
            artist_name=similar_track.artist_name,
            title=similar_track.track_name,
            album=similar_track.album_name,
            year="",
        )

    async def test_missing_tracks_when_not_in_provider(self):
        recommendation_provider = _make_recommendation_provider()
        seed_track = _make_recommendation_track(track_name="Seed Track")
        similar_track = _make_recommendation_track()
        recommendation_provider.get_top_tracks.return_value = [seed_track]
        recommendation_provider.get_similar_tracks.return_value = [similar_track]

        music_provider = _make_music_provider([])

        found, missing, provider_tracks = await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.top_tracks,
            num_recommendations=1,
            username="user",
            blend_users=None,
        )

        assert found == []
        assert missing == [similar_track]
        assert provider_tracks == []

    async def test_matching_track_skipped_when_not_in_provider(self):
        """A similar track already marked missing is skipped on a later encounter."""
        seed_track = _make_recommendation_track(track_name="Seed Track")
        similar_track = _make_recommendation_track()

        recommendation_provider = _make_recommendation_provider()
        recommendation_provider.get_top_tracks.return_value = [seed_track]
        recommendation_provider.get_similar_tracks.return_value = [
            similar_track,
            similar_track,
        ]

        music_provider = _make_music_provider([])

        found, missing, provider_tracks = await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.top_tracks,
            num_recommendations=5,
            username="user",
            blend_users=None,
        )

        assert found == []
        assert missing.count(similar_track) == 1
        assert provider_tracks == []


class TestFamiliarTracks:
    async def test_fills_a_quarter_of_recommendations_with_top_tracks(self):
        top_tracks = [
            _make_recommendation_track(track_name=f"Top Track {index}")
            for index in range(8)
        ]
        similar_tracks = [
            _make_recommendation_track(track_name=f"Similar Track {index}")
            for index in range(8)
        ]

        recommendation_provider = _make_recommendation_provider()
        recommendation_provider.get_top_tracks.return_value = top_tracks
        recommendation_provider.get_similar_tracks.return_value = similar_tracks

        music_provider = _make_music_provider_with_tracks(top_tracks + similar_tracks)

        found, missing, provider_tracks = await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.top_tracks,
            num_recommendations=8,
            username="user",
            blend_users=None,
        )

        familiar_tracks = [track for track in found if track in top_tracks]

        assert len(found) == 8
        assert len(familiar_tracks) == 2
        assert set(familiar_tracks) == {top_tracks[0], top_tracks[1]}
        assert len(provider_tracks) == 8
        assert missing == []

    async def test_familiar_track_still_seeds_similar_tracks(self):
        top_tracks = [
            _make_recommendation_track(track_name=f"Top Track {index}")
            for index in range(4)
        ]
        similar_track = _make_recommendation_track(track_name="Similar Track")

        recommendation_provider = _make_recommendation_provider()
        recommendation_provider.get_top_tracks.return_value = top_tracks
        recommendation_provider.get_similar_tracks.return_value = [similar_track]

        music_provider = _make_music_provider_with_tracks(top_tracks + [similar_track])

        found, _, _ = await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.top_tracks,
            num_recommendations=4,
            username="user",
            blend_users=None,
        )

        assert top_tracks[0] in found
        assert similar_track in found
        recommendation_provider.get_similar_tracks.assert_any_await(
            artist_name=top_tracks[0].artist_name,
            track_name=top_tracks[0].track_name,
            musicbrainz_id=top_tracks[0].musicbrainz_id,
        )

    async def test_familiar_track_missing_when_not_in_provider(self):
        top_tracks = [
            _make_recommendation_track(track_name=f"Top Track {index}")
            for index in range(4)
        ]

        recommendation_provider = _make_recommendation_provider()
        recommendation_provider.get_top_tracks.return_value = top_tracks
        recommendation_provider.get_similar_tracks.return_value = []

        music_provider = _make_music_provider_with_tracks([])

        found, missing, provider_tracks = await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.top_tracks,
            num_recommendations=4,
            username="user",
            blend_users=None,
        )

        assert found == []
        assert set(missing) == set(top_tracks)
        assert provider_tracks == []

    async def test_familiar_tracks_fill_slots_left_by_similar_tracks(self):
        top_tracks = [
            _make_recommendation_track(track_name=f"Top Track {index}")
            for index in range(8)
        ]
        similar_track = _make_recommendation_track(track_name="Similar Track")

        recommendation_provider = _make_recommendation_provider()
        recommendation_provider.get_top_tracks.return_value = top_tracks
        recommendation_provider.get_similar_tracks.return_value = [similar_track]

        music_provider = _make_music_provider_with_tracks(top_tracks + [similar_track])

        found, missing, provider_tracks = await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.top_tracks,
            num_recommendations=8,
            username="user",
            blend_users=None,
        )

        familiar_tracks = [track for track in found if track in top_tracks]

        assert len(found) == 8
        assert similar_track in found
        assert len(familiar_tracks) == 7
        assert len(provider_tracks) == 8
        assert missing == []

    async def test_no_familiar_tracks_when_quarter_rounds_to_zero(self):
        top_track = _make_recommendation_track(track_name="Top Track")
        similar_track = _make_recommendation_track(track_name="Similar Track")

        recommendation_provider = _make_recommendation_provider()
        recommendation_provider.get_top_tracks.return_value = [top_track]
        recommendation_provider.get_similar_tracks.return_value = [similar_track]

        music_provider = _make_music_provider_with_tracks([top_track, similar_track])

        found, missing, _ = await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.top_tracks,
            num_recommendations=1,
            username="user",
            blend_users=None,
        )

        assert found == [similar_track]
        assert missing == []
