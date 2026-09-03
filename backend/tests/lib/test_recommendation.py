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
        recommendation_provider.get_recent_tracks.assert_awaited_once_with(
            username="user", limit=10
        )
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
            username="user", limit=10
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
            username="user", limit=7
        )
        recommendation_provider.get_top_tracks.assert_awaited_once_with(
            username="user", limit=3
        )

    async def test_mixed_strategy_seeds_half_of_the_recent_tracks(self):
        """The recent tracks are fetched once and only half of them seed similar tracks."""
        recent_tracks = [
            _make_recommendation_track(track_name=f"Recent Track {index}")
            for index in range(10)
        ]

        recommendation_provider = _make_recommendation_provider()
        recommendation_provider.get_recent_tracks.return_value = recent_tracks
        music_provider = _make_music_provider()

        await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.mixed,
            num_recommendations=10,
            username="user",
            blend_users=None,
        )

        seeded_track_names = [
            await_call.kwargs["track_name"]
            for await_call in recommendation_provider.get_similar_tracks.await_args_list
        ]

        assert seeded_track_names == [track.track_name for track in recent_tracks[:5]]

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
            call(username="alice-prov", limit=10),
            call(username="bob-prov", limit=10),
        ]
        assert recommendation_provider.get_top_tracks.await_args_list == [
            call(username="alice-prov", limit=2),
            call(username="bob-prov", limit=2),
        ]

    async def test_blend_strategy_fills_from_every_blend_user(self):
        """The familiar tracks are drawn from all blend users, not just the requesting user."""
        alice_tracks = [
            _make_recommendation_track(track_name=f"Alice Track {index}")
            for index in range(4)
        ]
        bob_tracks = [
            _make_recommendation_track(track_name=f"Bob Track {index}")
            for index in range(4)
        ]
        recent_tracks_by_user = {
            "alice-prov": alice_tracks,
            "bob-prov": bob_tracks,
        }

        recommendation_provider = _make_recommendation_provider()
        recommendation_provider.get_recent_tracks = AsyncMock(
            side_effect=lambda *, username, limit: recent_tracks_by_user[username]
        )
        music_provider = _make_music_provider_with_tracks(alice_tracks + bob_tracks)

        found, missing, _ = await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.blend,
            num_recommendations=4,
            username="user",
            blend_users=[("alice", "alice-prov"), ("bob", "bob-prov")],
        )

        assert missing == []
        assert set(found) == {
            alice_tracks[0],
            bob_tracks[0],
            alice_tracks[1],
            bob_tracks[1],
        }

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
            username="carol_provider", limit=5
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
    async def test_fills_a_quarter_of_recommendations_with_recent_tracks(self):
        recent_tracks = [
            _make_recommendation_track(track_name=f"Recent Track {index}")
            for index in range(8)
        ]
        similar_tracks = [
            _make_recommendation_track(track_name=f"Similar Track {index}")
            for index in range(8)
        ]

        recommendation_provider = _make_recommendation_provider()
        recommendation_provider.get_top_tracks.return_value = [
            _make_recommendation_track(track_name="Top Track")
        ]
        recommendation_provider.get_recent_tracks.return_value = recent_tracks
        recommendation_provider.get_similar_tracks.return_value = similar_tracks

        music_provider = _make_music_provider_with_tracks(
            recent_tracks + similar_tracks
        )

        found, missing, provider_tracks = await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.top_tracks,
            num_recommendations=8,
            username="user",
            blend_users=None,
        )

        familiar_tracks = [track for track in found if track in recent_tracks]

        assert len(found) == 8
        assert len(familiar_tracks) == 2
        assert set(familiar_tracks) == {recent_tracks[0], recent_tracks[1]}
        assert len(provider_tracks) == 8
        assert missing == []

    async def test_familiar_track_still_seeds_similar_tracks(self):
        recent_tracks = [
            _make_recommendation_track(track_name=f"Recent Track {index}")
            for index in range(4)
        ]
        similar_track = _make_recommendation_track(track_name="Similar Track")

        recommendation_provider = _make_recommendation_provider()
        recommendation_provider.get_recent_tracks.return_value = recent_tracks
        recommendation_provider.get_similar_tracks.return_value = [similar_track]

        music_provider = _make_music_provider_with_tracks(
            recent_tracks + [similar_track]
        )

        found, _, _ = await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.recent_tracks,
            num_recommendations=4,
            username="user",
            blend_users=None,
        )

        assert recent_tracks[0] in found
        assert similar_track in found
        recommendation_provider.get_similar_tracks.assert_any_await(
            artist_name=recent_tracks[0].artist_name,
            track_name=recent_tracks[0].track_name,
            musicbrainz_id=recent_tracks[0].musicbrainz_id,
        )

    async def test_familiar_track_missing_when_not_in_provider(self):
        recent_tracks = [
            _make_recommendation_track(track_name=f"Recent Track {index}")
            for index in range(4)
        ]

        recommendation_provider = _make_recommendation_provider()
        recommendation_provider.get_recent_tracks.return_value = recent_tracks
        recommendation_provider.get_similar_tracks.return_value = []

        music_provider = _make_music_provider_with_tracks([])

        found, missing, provider_tracks = await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.recent_tracks,
            num_recommendations=4,
            username="user",
            blend_users=None,
        )

        assert found == []
        assert set(missing) == set(recent_tracks)
        assert provider_tracks == []

    async def test_familiar_tracks_fill_slots_left_by_recent_tracks(self):
        top_tracks = [
            _make_recommendation_track(track_name=f"Top Track {index}")
            for index in range(8)
        ]
        recent_tracks = [
            _make_recommendation_track(track_name=f"Recent Track {index}")
            for index in range(8)
        ]
        similar_track = _make_recommendation_track(track_name="Similar Track")

        recommendation_provider = _make_recommendation_provider()
        recommendation_provider.get_top_tracks.return_value = top_tracks
        recommendation_provider.get_recent_tracks.return_value = recent_tracks
        recommendation_provider.get_similar_tracks.return_value = [similar_track]

        music_provider = _make_music_provider_with_tracks(
            recent_tracks + [similar_track]
        )

        found, missing, provider_tracks = await get_recommendations(
            recommendation_provider=recommendation_provider,
            music_provider=music_provider,
            strategy=RecommendationStrategy.top_tracks,
            num_recommendations=8,
            username="user",
            blend_users=None,
        )

        familiar_tracks = [track for track in found if track in recent_tracks]

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
