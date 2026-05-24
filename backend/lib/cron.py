import logging
from typing import Callable
import uuid

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from lib.utils import parse_cron_expression

scheduler = AsyncIOScheduler()
scheduler.start()


logger = logging.getLogger(__name__)


def get_job(job_id: str | uuid.UUID):
    return scheduler.get_job(job_id=str(job_id))


def create_job(
    func: Callable,
    kwargs: dict,
    cron_expression: str,
    job_id: str | uuid.UUID,
) -> None:
    """Create a cron job with the given function, arguments, and cron expression.

    Args:
        func: The function to execute.
        kwargs: The keyword arguments to pass to the function when executed.
        cron_expression: The cron expression defining the schedule for the job.
        job_id: Unique identifier for the job.
    """
    job = get_job(job_id=job_id)

    if job:
        delete_job(job_id=job_id)

    logger.info(
        f"Creating cron job for {job_id} with cron expression: {cron_expression}"
    )
    scheduler.add_job(
        func=func,
        kwargs=kwargs,
        trigger="cron",
        id=job_id,
        **parse_cron_expression(cron_expression),
    )


def update_job(
    func: Callable,
    kwargs: dict,
    cron_expression: str,
    job_id: str | uuid.UUID,
):
    job = get_job(job_id=job_id)

    logger.info(
        f"Updating cron job for {job_id} with cron expression: {cron_expression}"
    )
    scheduler.add_job(
        func=func,
        kwargs=kwargs,
        trigger="cron",
        id=job_id,
        replace_existing=True if job else False,
        **parse_cron_expression(cron_expression),
    )


def delete_job(job_id: str | uuid.UUID):
    job = get_job(job_id=job_id)

    if job:
        logger.info(f"Deleting cron job for {job_id}")
        scheduler.remove_job(job_id=job_id)
