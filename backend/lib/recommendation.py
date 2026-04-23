import uuid
from typing import Any

from fastapi import HTTPException, status

from db.models.recommendation import (
    RecommendationProvider,
    RecommendationSession,
    RecommendationStatus,
    RecommendationStrategy,
    RecommendationTrackType,
)
from db.recommendation import (
    build_recommendation_session_tracks,
    create_recommendation_session,
    format_recommendation_session_track_names,
    get_recommendation_session_by_id,
    update_recommendation_session,
)
from db.session import SessionDep, get_isolated_session
from lib.common import (
    LastFMRecentTrack,
    LastFMTopTrack,
)
from lib.lastfm import (
    get_lastfm_recent_tracks,
    get_lastfm_similar_tracks,
    get_lastfm_top_tracks,
)
from lib.track import find_track
from lib.utils import get_now


def _get_recommendations(
    lastfm_username: str,
    strategy: RecommendationStrategy,
    num_recommendations: int,
) -> tuple[
    list[LastFMTopTrack | LastFMRecentTrack], list[LastFMTopTrack | LastFMRecentTrack]
]:
    """Get track recommendations for a user based on their listening history."""
    match strategy:
        case RecommendationStrategy.top_tracks:
            all_tracks = get_lastfm_top_tracks(
                user=lastfm_username,
                limit=num_recommendations,
            )
        case RecommendationStrategy.recent_tracks:
            all_tracks = get_lastfm_recent_tracks(
                user=lastfm_username,
                limit=num_recommendations,
            )
        case RecommendationStrategy.mixed:
            recent_tracks = get_lastfm_recent_tracks(
                user=lastfm_username,
                limit=round(num_recommendations * 0.7),
            )
            top_tracks = get_lastfm_top_tracks(
                user=lastfm_username,
                limit=round(num_recommendations * 0.3),
            )
            all_tracks = recent_tracks + top_tracks
    missing: set[LastFMTopTrack | LastFMRecentTrack] = set()
    found: set[LastFMTopTrack | LastFMRecentTrack] = set()

    for track in all_tracks:
        similar_tracks = get_lastfm_similar_tracks(
            user=lastfm_username,
            artist=track.artist_name,
            track=track.track_name,
        )

        for similar_track in similar_tracks:
            jellyfin_track = find_track(
                artist_name=similar_track.artist_name,
                track_name=similar_track.track_name,
                album_name="",
                year="",
                duration=similar_track.duration,
            )

            if jellyfin_track.is_not_found():
                missing.add(track)
            else:
                found.add(track)
                break
    return list(found), list(missing)


def generate_recommendations_task(
    lastfm_username: str,
    recommendation_session_id: uuid.UUID,
) -> Any:
    """Get track recommendations for a user based on their listening history in a background task."""

    with get_isolated_session() as session:
        recommendation_session = get_recommendation_session_by_id(
            session=session, recommendation_session_id=recommendation_session_id
        )
        if not recommendation_session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to find recommendation session: {recommendation_session_id}",
            )

        started_at = recommendation_session.started_at

        try:
            recommendation_session.status = RecommendationStatus.pending
            update_recommendation_session(
                session=session, recommendation_session=recommendation_session
            )

            found_tracks, missing_tracks = _get_recommendations(
                lastfm_username=lastfm_username,
                strategy=recommendation_session.strategy,
                num_recommendations=recommendation_session.requested_count,
            )
            all_tracks = found_tracks + missing_tracks

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
            raise


def generate_recommendations(
    username: str,
    session: SessionDep,
    num_recommendations: int = 50,
) -> dict[str, str]:
    """Get track recommendations for a user based on their listening history."""
    started_at = get_now()
    recommendation_session = RecommendationSession(
        username=username,
        provider=RecommendationProvider.lastfm,
        strategy=RecommendationStrategy.recent_tracks,
        requested_count=num_recommendations,
        generated_count=0,
        started_at=started_at,
        finished_at=started_at,
        duration_seconds=0,
        status=RecommendationStatus.pending,
    )
    create_recommendation_session(
        session=session, recommendation_session=recommendation_session
    )

    generate_recommendations_task(
        lastfm_username=username,
        recommendation_session_id=recommendation_session.id,
    )
    return {"id": str(recommendation_session.id)}
