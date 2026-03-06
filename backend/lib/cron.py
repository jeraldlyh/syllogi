import logging
from typing import Callable, cast
import uuid

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db.models.playlist import Playlist
from lib.utils import _parse_cron_expression

scheduler = AsyncIOScheduler()
scheduler.start()


logger = logging.getLogger(__name__)


def _get_job(playlist_id: str | uuid.UUID):
    return scheduler.get_job(job_id=playlist_id)


def _create_job(func: Callable, kwargs: dict, cron_expression: str):
    playlist_id = str(cast(Playlist, kwargs.get("playlist")).id)
    job = _get_job(playlist_id=playlist_id)

    if job:
        _delete_job(playlist_id=playlist_id)

    logger.info(
        f"Creating cron job for playlist {playlist_id} with cron expression: {cron_expression}"
    )
    scheduler.add_job(
        func=func,
        kwargs=kwargs,
        trigger="cron",
        id=str(playlist_id),
        **_parse_cron_expression(cron_expression),
    )


def _update_job(func: Callable, kwargs: dict, cron_expression: str):
    playlist_id = str(cast(Playlist, kwargs.get("playlist")).id)
    job = _get_job(playlist_id=playlist_id)

    logger.info(
        f"Updating cron job for playlist {playlist_id} with cron expression: {cron_expression}"
    )
    scheduler.add_job(
        func=func,
        kwargs=kwargs,
        trigger="cron",
        id=playlist_id,
        replace_existing=True if job else False,
        **_parse_cron_expression(cron_expression),
    )


def _delete_job(playlist_id: str | uuid.UUID):
    job = _get_job(playlist_id=playlist_id)

    if job:
        logger.info(f"Deleting cron job for playlist {playlist_id}")
        scheduler.remove_job(job_id=playlist_id)
