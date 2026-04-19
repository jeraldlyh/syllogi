from typing import Annotated

from fastapi import APIRouter, Query

from lib.recommendation import get_recommendations_task

router = APIRouter()


@router.get(
    path="",
    summary="Get track recommendations",
    description="Get track recommendations based on a given track.",
)
def _get_recommendations(
    user: Annotated[str, Query(description="LastFM username")],
):
    result = get_recommendations_task(user=user)

    return result
