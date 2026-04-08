import os
from fastapi import APIRouter

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
    AUTH_AUTHENTIK_ID = os.getenv("AUTH_AUTHENTIK_ID")
    AUTH_AUTHENTIK_SECRET = os.getenv("AUTH_AUTHENTIK_SECRET")
    AUTH_AUTHENTIK_ISSUER = os.getenv("AUTH_AUTHENTIK_ISSUER")
    return {
        "is_oauth_enabled": bool(
            AUTH_AUTHENTIK_ID and AUTH_AUTHENTIK_SECRET and AUTH_AUTHENTIK_ISSUER
        )
    }
