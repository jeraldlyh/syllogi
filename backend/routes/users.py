from fastapi import APIRouter
from lib.providers import get_provider

router = APIRouter()


@router.get(
    path="",
    summary="Get music server users",
    description="Retrieve a list of all users from the configured music server.",
    responses={
        200: {
            "description": "Users retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {"id": "a8f1b0c2", "name": "jerald"},
                            {"id": "9f8e7d6c", "name": "guest"},
                        ],
                    }
                }
            },
        }
    },
)
async def _get_users():
    provider = get_provider()
    users = await provider.get_users()

    return [user.to_dict() for user in users]
