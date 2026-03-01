from fastapi import APIRouter

from lib.cron import scheduler

router = APIRouter()


@router.get(
    path="", summary="Get cron jobs", description="Retrieve a list of all cron jobs."
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
