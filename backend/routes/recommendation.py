from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from db.models.recommendation import (
    Recommendation,
    RecommendationProvider,
    RecommendationSession,
    RecommendationStatus,
    RecommendationStrategy,
)
from db.recommendation import (
    create_recommendation_session,
    create_recommendation,
    delete_recommendation,
    get_recommendation_by_id,
    get_recommendations,
    update_recommendation,
)
from db.session import SessionDep
from lib.jellyfin import get_jellyfin_users
from lib.recommendation import get_recommendations_task
from lib.utils import get_now

router = APIRouter()


class CreateOrUpdateRecommendationRequest(BaseModel):
    username: str
    strategy: RecommendationStrategy
    lastfm_username: str
    requested_count: int = Field(default=50, ge=1, le=50)


@router.get(
    path="",
    summary="Get recommendation settings",
    description="Retrieve a list of all recommendation settings.",
)
def _get_recommendation_settings(session: SessionDep) -> list[dict]:
    recommendations = get_recommendations(session=session)

    return [recommendation.to_dict() for recommendation in recommendations]


@router.post(
    path="",
    summary="Create recommendation",
    description="Create recommendation for a Jellyfin user.",
)
def _create_recommendation_setting(
    item: CreateOrUpdateRecommendationRequest,
    session: SessionDep,
) -> dict[str, str]:
    recommendation = Recommendation(
        username=item.username,
        strategy=item.strategy,
        lastfm_username=item.lastfm_username,
        requested_count=item.requested_count,
    )
    create_recommendation(session=session, recommendation_setting=recommendation)

    return {"id": str(recommendation.id)}


@router.put(
    path="/{recommendation_id}",
    summary="Update recommendation",
    description="Update recommendation by ID.",
)
def _update_recommendation_setting(
    recommendation_id: str,
    item: CreateOrUpdateRecommendationRequest,
    session: SessionDep,
) -> dict[str, str]:
    recommendation = get_recommendation_by_id(
        session=session, recommendation_id=recommendation_id
    )

    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to find recommendation : {recommendation_id}",
        )

    recommendation.username = item.username
    recommendation.strategy = item.strategy
    recommendation.lastfm_username = item.lastfm_username
    recommendation.requested_count = item.requested_count

    update_recommendation(
        session=session,
        recommendation_setting=recommendation,
    )

    return {"message": "Recommendation updated successfully"}


@router.delete(
    path="/{recommendation_id}",
    summary="Delete recommendation",
    description="Delete recommendation by ID.",
)
def _delete_recommendation(
    recommendation_id: str,
    session: SessionDep,
) -> dict[str, str]:
    recommendation = get_recommendation_by_id(
        session=session, recommendation_id=recommendation_id
    )

    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to find recommendation setting: {recommendation_id}",
        )

    delete_recommendation(session=session, recommendation_setting=recommendation)

    return {"message": "Recommendation deleted successfully"}


@router.post(
    path="/generate",
    summary="Generate track recommendations",
    description="Generate track recommendations for a user based on their listening history.",
)
async def generate_recommendations(
    recommendation: Recommendation,
    background_tasks: BackgroundTasks,
    session: SessionDep,
) -> dict[str, str]:
    username = recommendation.username
    jellyfin_users = get_jellyfin_users()

    if not any(jellyfin_user.name == username for jellyfin_user in jellyfin_users):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unable to find Jellyfin user: {username}",
        )

    started_at = get_now()
    recommendation_session = RecommendationSession(
        username=username,
        provider=RecommendationProvider.lastfm,
        strategy=recommendation.strategy,
        requested_count=recommendation.requested_count,
        generated_count=0,
        started_at=started_at,
        finished_at=started_at,
        duration_seconds=0,
        status=RecommendationStatus.pending,
    )
    create_recommendation_session(
        session=session,
        recommendation_session=recommendation_session,
    )

    background_tasks.add_task(
        get_recommendations_task,
        username=username,
        lastfm_username=recommendation.lastfm_username,
        recommendation_session=recommendation_session,
    )

    return {"id": str(recommendation_session.id)}
