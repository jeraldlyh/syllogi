import asyncio
import uuid
from unittest.mock import MagicMock

import pytest

from lib.cron import create_job, delete_job, get_job, scheduler, update_job


@pytest.fixture(scope="module", autouse=True)
def _event_loop():
    loop = asyncio.new_event_loop()

    yield loop

    loop.close()


@pytest.fixture(autouse=True)
def _scheduler(_event_loop):
    scheduler._eventloop = _event_loop

    if not scheduler.running:
        scheduler.start()
    yield

    scheduler.remove_all_jobs()


class TestGetJob:
    def test_missing_job_returns_none(self):
        assert get_job(job_id=uuid.uuid4()) is None


class TestCreateJob:
    def test_creates_job_retrievable_with_get_job(self):
        job_id = str(uuid.uuid4())

        create_job(
            func=MagicMock(), kwargs={}, cron_expression="0 0 * * *", job_id=job_id
        )

        assert get_job(job_id=job_id) is not None

    def test_replaces_existing_job_with_same_id(self):
        job_id = str(uuid.uuid4())

        create_job(
            func=MagicMock(), kwargs={}, cron_expression="0 0 * * *", job_id=job_id
        )

        assert len(scheduler.get_jobs()) == 1

        create_job(
            func=MagicMock(), kwargs={}, cron_expression="30 5 * * *", job_id=job_id
        )

        assert len(scheduler.get_jobs()) == 1


class TestUpdateJob:
    def test_updates_existing_job(self):
        job_id = str(uuid.uuid4())

        create_job(
            func=MagicMock(), kwargs={}, cron_expression="0 0 * * *", job_id=job_id
        )

        job = get_job(job_id=job_id)
        assert job is not None
        assert "minute='0'" in str(job.trigger)

        update_job(
            func=MagicMock(), kwargs={}, cron_expression="30 5 * * *", job_id=job_id
        )

        job = get_job(job_id=job_id)
        assert job is not None
        assert "minute='30'" in str(job.trigger)


class TestDeleteJob:
    def test_removes_job(self):
        job_id = str(uuid.uuid4())
        create_job(
            func=MagicMock(), kwargs={}, cron_expression="0 0 * * *", job_id=job_id
        )

        assert get_job(job_id=job_id) is not None

        delete_job(job_id=job_id)

        assert get_job(job_id=job_id) is None

    def test_noop_for_missing_job(self):
        delete_job(job_id=str(uuid.uuid4()))

        assert len(scheduler.get_jobs()) == 0
