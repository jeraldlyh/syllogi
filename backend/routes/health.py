from fastapi import APIRouter

from lib.env import is_slskd_configured
from lib.slskd import _slskd

router = APIRouter()


@router.get(
    path="/health",
    summary="Health check",
    description="Check if the API is healthy.",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {"example": {"success": True, "data": "ok"}}
            },
        }
    },
)
async def health():
    return "ok"


@router.get(
    path="/health/slskd",
    summary="slskd health check",
    description="Check if slskd is configured, reachable, and authenticated.",
    responses={
        200: {
            "description": "slskd status",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "configured": True,
                            "connected": True,
                        },
                    }
                }
            },
        }
    },
)
async def slskd_health():
    if not is_slskd_configured():
        return {"configured": False, "connected": False}

    try:
        await _slskd("/health")
        return {"configured": True, "connected": True}
    except Exception:
        return {"configured": True, "connected": False}
