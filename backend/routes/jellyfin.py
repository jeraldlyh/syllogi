from fastapi import APIRouter
from lib.jellyfin import _get_jellyfin_users

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
async def get_jellyfin_users():
    users = _get_jellyfin_users()

    return [
        {
            "id": user.get("Id"),
            "name": user.get("Name"),
        }
        for user in users
    ]
