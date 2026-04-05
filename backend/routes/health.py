from fastapi import APIRouter

router = APIRouter()


@router.get(
    path="/health", summary="Health check", description="Check if the API is healthy."
)
async def health():
    return "ok"
