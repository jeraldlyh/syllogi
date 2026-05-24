import asyncio
import logging
import uuid
from typing import Any

from fastapi import HTTPException, status

from db.models.recommendation import (
    Recommendation,
    RecommendationProvider,
    RecommendationSession,
    RecommendationStatus,
    RecommendationStrategy,
    RecommendationTrackType,
)
from db.recommendation import get_recommendation_by_id
from db.recommendation_session import (
    build_recommendation_session_tracks,
    create_recommendation_session,
    format_recommendation_session_track_names,
    get_recommendation_session_by_id,
    update_recommendation_session,
)
from db.session import get_isolated_session
from lib.download import download_missing_tracks
from lib.jellyfin import (
    add_songs_to_jellyfin_playlist,
    delete_songs_from_jellyfin_playlist,
    get_jellyfin_playlist_songs,
    get_or_create_jellyfin_playlist,
    is_jellyfin_scanning_library,
    rescan_jellyfin_library,
)
from lib.models.jellyfin import JellyfinTrack
from lib.models.lastfm import (
    LastFMSimilarTrack,
)
from lib.lastfm import (
    get_lastfm_recent_tracks,
    get_lastfm_similar_tracks,
    get_lastfm_top_tracks,
)
from lib.track import find_track, reconcile_after_download, resolve_tracks
from lib.utils import get_now

logger = logging.getLogger(__name__)


async def get_recommendations(
    lastfm_username: str,
    strategy: RecommendationStrategy,
    num_recommendations: int,
) -> tuple[list[LastFMSimilarTrack], list[LastFMSimilarTrack], list[JellyfinTrack]]:
    """Get track recommendations for a user based on their listening history."""
    match strategy:
        case RecommendationStrategy.top_tracks:
            all_tracks = await get_lastfm_top_tracks(
                user=lastfm_username,
                limit=num_recommendations,
            )
        case RecommendationStrategy.recent_tracks:
            all_tracks = await get_lastfm_recent_tracks(
                user=lastfm_username,
                limit=num_recommendations,
            )
        case RecommendationStrategy.mixed:
            recent_tracks = await get_lastfm_recent_tracks(
                user=lastfm_username,
                limit=round(num_recommendations * 0.7),
            )
            top_tracks = await get_lastfm_top_tracks(
                user=lastfm_username,
                limit=round(num_recommendations * 0.3),
            )
            all_tracks = recent_tracks + top_tracks
    missing: set[LastFMSimilarTrack] = set()
    found: set[LastFMSimilarTrack] = set()
    jellyfin_tracks = []

    for track in all_tracks:
        similar_tracks = await get_lastfm_similar_tracks(
            user=lastfm_username,
            artist=track.artist_name,
            track=track.track_name,
        )

        has_missing = False
        for similar_track in similar_tracks:
            if similar_track in found:
                continue

            jellyfin_track = await find_track(
                artist_name=similar_track.artist_name,
                track_name=similar_track.track_name,
                album_name="",
                year="",
                duration=similar_track.duration,
            )
            if not has_missing and jellyfin_track.is_not_found():
                missing.add(similar_track)
                has_missing = True
            else:
                found.add(similar_track)
                jellyfin_tracks.append(jellyfin_track)
                break

    return list(found), list(missing), jellyfin_tracks


async def generate_recommendations_task(
    lastfm_username: str,
    recommendation_session_id: uuid.UUID,
) -> Any:
    """Get track recommendations for a user based on their listening history in a background task."""

    with get_isolated_session() as session:
        logger.info(
            f"Generating recommendations for user {lastfm_username} with session ID {recommendation_session_id}"
        )
        recommendation_session = get_recommendation_session_by_id(
            session=session, recommendation_session_id=recommendation_session_id
        )
        if not recommendation_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unable to find recommendation session: {recommendation_session_id}",
            )

        started_at = recommendation_session.started_at

        try:
            recommendation_session.status = RecommendationStatus.pending
            update_recommendation_session(
                session=session, recommendation_session=recommendation_session
            )

            found_tracks, missing_tracks, jellyfin_tracks = await get_recommendations(
                lastfm_username=lastfm_username,
                strategy=recommendation_session.strategy,
                num_recommendations=recommendation_session.requested_count,
            )
            all_tracks = found_tracks + missing_tracks

            logger.info(
                f"Found {len(found_tracks)} tracks and {len(missing_tracks)} missing tracks for user {lastfm_username}"
            )
            if missing_tracks:
                downloaded_tracks, still_missing_tracks = await download_missing_tracks(
                    missing_tracks=[
                        track.to_external_track() for track in missing_tracks
                    ]
                )

                if downloaded_tracks:
                    logger.info(f"Downloaded {len(downloaded_tracks)} missing songs")

                    await rescan_jellyfin_library()
                    await asyncio.sleep(3)

                    while await is_jellyfin_scanning_library():
                        logger.info(
                            "Waiting for Jellyfin to finish scanning library..."
                        )
                        await asyncio.sleep(15)

                    (
                        found_tracks_after_download,
                        missing_tracks_after_scan,
                    ) = await resolve_tracks(tracks=downloaded_tracks)

                    found_tracks, missing_tracks = reconcile_after_download(
                        found_tracks=found_tracks,
                        found_tracks_after_download=found_tracks_after_download,
                        missing_tracks=missing_tracks,
                        missing_tracks_after_download=still_missing_tracks,
                        missing_tracks_after_scan=missing_tracks_after_scan,
                        get_key=lambda t: (t.artist_name, t.track_name),
                    )

            finished_at = get_now()
            recommendation_session.status = RecommendationStatus.completed
            recommendation_session.finished_at = finished_at
            recommendation_session.duration_seconds = int(
                finished_at.timestamp() - started_at.timestamp()
            )
            recommendation_session.generated_count = len(found_tracks)
            recommendation_session.tracks = (
                build_recommendation_session_tracks(
                    recommendation_session_id=recommendation_session_id,
                    names=format_recommendation_session_track_names(found_tracks),
                    type=RecommendationTrackType.matched,
                )
                + build_recommendation_session_tracks(
                    recommendation_session_id=recommendation_session_id,
                    names=format_recommendation_session_track_names(missing_tracks),
                    type=RecommendationTrackType.missing,
                )
                + build_recommendation_session_tracks(
                    recommendation_session_id=recommendation_session_id,
                    names=format_recommendation_session_track_names(all_tracks),
                    type=RecommendationTrackType.total,
                )
            )

            update_recommendation_session(
                session=session, recommendation_session=recommendation_session
            )

            if not found_tracks:
                logger.info("No tracks found in Jellyfin for recommendations")
                return

            jellyfin_track_ids = [track.id for track in jellyfin_tracks]

            if not jellyfin_track_ids:
                logger.info(
                    "No tracks from recommendations could be resolved to Jellyfin IDs"
                )
                return

            logger.info(
                f"Creating Jellyfin playlist with {len(jellyfin_track_ids)} tracks"
            )

            playlist_id, jellyfin_user_id = await get_or_create_jellyfin_playlist(
                playlist_name="Daily Recommendations",
                username=recommendation_session.username,
            )

            existing_tracks = await get_jellyfin_playlist_songs(
                playlist_id=playlist_id,
                user_id=jellyfin_user_id,
            )

            if existing_tracks:
                await delete_songs_from_jellyfin_playlist(
                    playlist_id=playlist_id,
                    track_ids=[track.id for track in existing_tracks],
                )

            await add_songs_to_jellyfin_playlist(
                playlist_id=playlist_id,
                user_id=jellyfin_user_id,
                track_ids=jellyfin_track_ids,
            )

        except Exception as e:
            finished_at = get_now()
            recommendation_session.status = RecommendationStatus.failed
            recommendation_session.finished_at = finished_at
            recommendation_session.duration_seconds = int(
                finished_at.timestamp() - started_at.timestamp()
            )
            recommendation_session.error_message = str(e)

            update_recommendation_session(
                session=session, recommendation_session=recommendation_session
            )


async def generate_recommendations(
    recommendation: Recommendation,
) -> dict[str, str]:
    """Get track recommendations for a user based on their listening history."""
    with get_isolated_session() as session:
        internal_recommendation = get_recommendation_by_id(
            session=session, recommendation_id=recommendation.id
        )

        if not internal_recommendation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to find recommendation setting: {recommendation.id}",
            )

        started_at = get_now()
        recommendation_session = RecommendationSession(
            username=internal_recommendation.username,
            provider=RecommendationProvider.lastfm,  # TODO: Support multiple providers
            strategy=internal_recommendation.strategy,
            requested_count=internal_recommendation.requested_count,
            generated_count=0,
            started_at=started_at,
            finished_at=started_at,
            duration_seconds=0,
            status=RecommendationStatus.pending,
        )
        create_recommendation_session(
            session=session, recommendation_session=recommendation_session
        )

        logger.info(
            f"Scheduling background task to generate recommendations for user {internal_recommendation.username} with session ID {recommendation_session.id}"
        )
        await generate_recommendations_task(
            lastfm_username=internal_recommendation.lastfm_username,
            recommendation_session_id=recommendation_session.id,
        )
        return {"id": str(recommendation_session.id)}
