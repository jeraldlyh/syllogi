from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from db.models.recommendation import (
    RecommendationProvider,
    RecommendationSession,
    Recommendation,
    RecommendationStatus,
    RecommendationStrategy,
)
from db.recommendation import create_recommendation_session, get_recommendation_sessions
from db.session import SessionDep
from lib.jellyfin import get_jellyfin_users
from lib.recommendation import get_recommendations_task
from lib.utils import get_now

router = APIRouter()


@router.get(
    path="",
    summary="Get recommendation sessions",
    description="Retrieve a list of all recommendation sessions.",
)
def _get_recommendation_sessions(session: SessionDep) -> list[dict]:
    recommendation_sessions = get_recommendation_sessions(session=session)

    return [
        recommendation_session.to_dict()
        for recommendation_session in recommendation_sessions
    ]


@router.post(
    path="/generate",
    summary="Generate track recommendations",
    description="Generate track recommendations for a user based on their listening history.",
)
async def generate_recommendations(
    recommendation: Recommendation,
    background_tasks: BackgroundTasks,
    session: SessionDep,
):
    username = recommendation.username
    jellyfin_users = get_jellyfin_users()

    if not any(jellyfin_user.name == username for jellyfin_user in jellyfin_users):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unable to find Jellyfin user: {username}",
        )

    started_at = get_now()
    default_num_recommendations = 50
    recommendation_session = RecommendationSession(
        username=username,
        provider=RecommendationProvider.lastfm,
        strategy=RecommendationStrategy.recent_tracks,
        requested_count=default_num_recommendations,
        generated_count=0,
        started_at=started_at,
        finished_at=started_at,
        duration_seconds=0,
        status=RecommendationStatus.pending,
    )
    create_recommendation_session(
        session=session, recommendation_session=recommendation_session
    )

    background_tasks.add_task(
        get_recommendations_task,
        username=username,
        recommendation_session=recommendation_session,
    )

    return {"id": str(recommendation_session.id)}
