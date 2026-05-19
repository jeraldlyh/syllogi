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
    create_recommendation,
    delete_recommendation,
    get_recommendation_by_id,
    get_recommendations,
    update_recommendation,
)
from db.recommendation_session import create_recommendation_session
from db.session import SessionDep
from lib.cron import create_job, delete_job, update_job
from lib.recommendation import (
    generate_recommendations,
    generate_recommendations_task,
)
from lib.utils import get_now

router = APIRouter()


class CreateOrUpdateRecommendationRequest(BaseModel):
    username: str
    strategy: RecommendationStrategy
    lastfm_username: str
    requested_count: int = Field(default=50, ge=1, le=50)
    cron_expression: str = ""


@router.get(
    path="",
    summary="Get recommendation settings",
    description="Retrieve a list of all recommendation settings.",
    responses={
        200: {
            "description": "List of recommendation settings retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "2baf7b6b-87de-4289-bdd8-42f138f8c9e1",
                            "username": "johndoe",
                            "strategy": "mixed",
                            "lastfm_username": "john_lastfm",
                            "requested_count": 50,
                            "cron_expression": "0 0 * * *",
                        }
                    ]
                }
            },
        },
    },
)
def _get_recommendation(session: SessionDep) -> list[dict]:
    recommendations = get_recommendations(session=session)

    return [recommendation.to_dict() for recommendation in recommendations]


@router.post(
    path="",
    summary="Create recommendation",
    description="Create recommendation for a Jellyfin user.",
    responses={
        200: {
            "description": "Recommendation created successfully",
            "content": {
                "application/json": {
                    "example": {"id": "2baf7b6b-87de-4289-bdd8-42f138f8c9e1"}
                }
            },
        },
    },
)
def _create_recommendation(
    item: CreateOrUpdateRecommendationRequest,
    session: SessionDep,
) -> dict[str, str]:
    recommendation = Recommendation(
        username=item.username,
        strategy=item.strategy,
        lastfm_username=item.lastfm_username,
        requested_count=item.requested_count,
        cron_expression=item.cron_expression,
    )

    create_recommendation(session=session, recommendation_setting=recommendation)
    create_job(
        func=generate_recommendations,
        kwargs={
            "username": recommendation.username,
            "session": session,
            "requested_count": recommendation.requested_count,
        },
        cron_expression=item.cron_expression,
        job_id=str(recommendation.id),
    )

    return {"id": str(recommendation.id)}


@router.put(
    path="/{recommendation_id}",
    summary="Update recommendation",
    description="Update recommendation by ID.",
    responses={
        200: {
            "description": "Recommendation updated successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Recommendation updated successfully"}
                }
            },
        },
        400: {
            "description": "Recommendation not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unable to find recommendation : <recommendation_id>"
                    }
                }
            },
        },
    },
)
def _update_recommendation(
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
    recommendation.cron_expression = item.cron_expression

    update_recommendation(
        session=session,
        recommendation_setting=recommendation,
    )
    update_job(
        func=generate_recommendations,
        kwargs={
            "username": recommendation.lastfm_username,
            "session": session,
            "requested_count": recommendation.requested_count,
        },
        cron_expression=item.cron_expression,
        job_id=str(recommendation_id),
    )

    return {"message": "Recommendation updated successfully"}


@router.delete(
    path="/{recommendation_id}",
    summary="Delete recommendation",
    description="Delete recommendation by ID.",
    responses={
        200: {
            "description": "Recommendation deleted successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Recommendation deleted successfully"}
                }
            },
        },
        400: {
            "description": "Recommendation not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unable to find recommendation setting: <recommendation_id>"
                    }
                }
            },
        },
    },
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
    delete_job(job_id=str(recommendation_id))

    return {"message": "Recommendation deleted successfully"}


@router.post(
    path="/generate",
    summary="Generate track recommendations",
    description="Generate track recommendations for a user based on their listening history.",
    responses={
        200: {
            "description": "Recommendation session created",
            "content": {
                "application/json": {
                    "example": {
                        "id": "2baf7b6b-87de-4289-bdd8-42f138f8c9e1",
                    }
                }
            },
        },
    },
)
def _generate_recommendations(
    recommendation: Recommendation,
    background_tasks: BackgroundTasks,
    session: SessionDep,
) -> dict[str, str]:
    username = recommendation.username
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
        generate_recommendations_task,
        lastfm_username=recommendation.lastfm_username,
        recommendation_session_id=recommendation_session.id,
    )

    return {"id": str(recommendation_session.id)}
