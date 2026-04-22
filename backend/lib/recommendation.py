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
    update_recommendation_session,
)
from db.session import SessionDep, get_isolated_session
from lib.common import (
    LastFMRecentTrack,
    LastFMTopTrack,
)
from lib.jellyfin import get_jellyfin_users
from lib.lastfm import (
    get_lastfm_recent_tracks,
    get_lastfm_similar_tracks,
    get_lastfm_top_tracks,
)
from lib.track import find_track
from lib.utils import get_now


def _get_recommendations(
    username: str, num_recommendations: int
) -> tuple[
    list[LastFMTopTrack | LastFMRecentTrack], list[LastFMTopTrack | LastFMRecentTrack]
]:
    """Get track recommendations for a user based on their listening history."""
    recent_tracks = get_lastfm_recent_tracks(
        user=username, limit=round(num_recommendations * 0.7)
    )
    top_tracks = get_lastfm_top_tracks(
        user=username, limit=round(num_recommendations * 0.3)
    )
    all_tracks = recent_tracks + top_tracks
    missing: set[LastFMTopTrack | LastFMRecentTrack] = set()
    found: set[LastFMTopTrack | LastFMRecentTrack] = set()

    for track in all_tracks:
        similar_tracks = get_lastfm_similar_tracks(
            user=username, artist=track.artist_name, track=track.track_name
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


async def get_recommendations_task(
    username: str, recommendation_session: RecommendationSession
) -> Any:
    """Get track recommendations for a user based on their listening history in a background task."""

    with get_isolated_session() as session:
        started_at = recommendation_session.started_at
        recommendation_session_id = recommendation_session.id

        try:
            recommendation_session.status = RecommendationStatus.pending
            update_recommendation_session(
                session=session, recommendation_session=recommendation_session
            )

            found_tracks, missing_tracks = _get_recommendations(
                username=username,
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


async def get_recommendations(
    user: str,
    session: SessionDep,
    num_recommendations: int = 50,
) -> dict[str, str]:
    """Get track recommendations for a user based on their listening history."""
    jellyfin_users = get_jellyfin_users()

    # if not any(jellyfin_user.name == user for jellyfin_user in jellyfin_users):
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"Unable to find Jellyfin user: {user}",
    #     )

    started_at = get_now()
    recommendation_session = RecommendationSession(
        username=user,
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
    session.expunge(recommendation_session)

    await get_recommendations_task(
        username=user, recommendation_session=recommendation_session
    )
    return {"id": str(recommendation_session.id)}
