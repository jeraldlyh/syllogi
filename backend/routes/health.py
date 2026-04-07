from fastapi import APIRouter

router = APIRouter()


@router.get(
    path="/health",
    summary="Health check",
    description="Check if the API is healthy.",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {"success": True, "data": "ok"}
                }
            },
        }
    },
)
async def health():
    return "ok"
