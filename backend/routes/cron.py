from fastapi import APIRouter

from lib.cron import scheduler

router = APIRouter()


@router.get(
    path="",
    summary="Get cron jobs",
    description="Retrieve a list of all cron jobs.",
    responses={
        200: {
            "description": "Cron jobs retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "id": "playlist-sync-1",
                                "name": "playlist-sync-1",
                                "next_run_time": "2026-04-05T15:00:00+00:00",
                            }
                        ],
                    }
                }
            },
        }
    },
)
async def get_cron_jobs():
    schedules = []

    for job in scheduler.get_jobs():
        schedule = {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat()
            if job.next_run_time
            else None,
        }
        schedules.append(schedule)
    return schedules
