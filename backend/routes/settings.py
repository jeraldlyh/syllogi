from fastapi import APIRouter
from lib.authentik import _get_authentik_config

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
    authentik_config = _get_authentik_config()

    return {
        "is_oauth_enabled": bool(
            authentik_config.get("client_id")
            and authentik_config.get("client_secret")
            and authentik_config.get("issuer")
        )
    }
