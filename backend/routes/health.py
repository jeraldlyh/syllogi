from fastapi import APIRouter

router = APIRouter()


@router.get(path="/health")
async def health():
    return "ok"
