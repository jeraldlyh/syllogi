from fastapi import APIRouter

from lib.logs import read_logs

router = APIRouter()


@router.get(
    path="",
    summary="Get logs",
    description="Retrieve the most recent backend log records from the log file.",
    responses={
        200: {
            "description": "Logs retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "timestamp": "2026-04-05T11:22:33+00:00",
                                "level": "INFO",
                                "module": "sync",
                                "message": "Playlist sync finished successfully",
                            }
                        ],
                    }
                }
            },
        }
    },
)
async def _get_logs(limit: int = 500):
    return read_logs(limit=limit)
