from fastapi import APIRouter
from lib.jellyfin import get_jellyfin_users

router = APIRouter()


@router.get(
    path="/users",
    summary="Get Jellyfin users",
    description="Retrieve a list of all Jellyfin users.",
    responses={
        200: {
            "description": "Jellyfin users retrieved successfully",
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
async def _get_jellyfin_users():
    users = await get_jellyfin_users()

    return [user.to_dict() for user in users]
