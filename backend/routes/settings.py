from fastapi import APIRouter
from lib.env import is_oauth_configured, is_slskd_configured

router = APIRouter()


@router.get(
    path="",
    summary="Get settings",
    description="Retrieve application settings, including authentication configuration.",
    responses={
        200: {
            "description": "Settings retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {"is_oauth_enabled": True},
                    }
                }
            },
        }
    },
)
def settings():
    return {
        "is_oauth_enabled": is_oauth_configured(),
        "is_slskd_enabled": is_slskd_configured(),
    }
