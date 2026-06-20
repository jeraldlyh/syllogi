from fastapi import APIRouter
from lib.env import is_jellyfin_configured, is_navidrome_configured, is_oauth_configured, is_slskd_configured

router = APIRouter()


def _get_music_providers() -> list[str]:
    providers = []
    if is_jellyfin_configured():
        providers.append("jellyfin")
    if is_navidrome_configured():
        providers.append("navidrome")
    return providers


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
        "music_providers": _get_music_providers(),
    }
