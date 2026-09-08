import json
import logging
from logging.handlers import RotatingFileHandler

import pytest

from lib import logs
from lib.logs import JsonFormatter, read_logs


@pytest.fixture(name="log_file")
def log_file_fixture(tmp_path, monkeypatch):
    path = tmp_path / "syllogi.log"
    monkeypatch.setattr(logs, "LOG_FILE", str(path))
    return path


def _isolated_logger(name: str, path) -> logging.Logger:
    handler = RotatingFileHandler(str(path))
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger(name)
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)
    return logger


def test_read_logs_returns_written_records(log_file):
    logger = _isolated_logger("test_logs_write", log_file)

    logger.warning("something happened")

    records = read_logs()

    assert len(records) == 1
    assert records[0]["level"] == "WARNING"
    assert records[0]["module"] == "test_logs"
    assert records[0]["message"] == "something happened"
    assert records[0]["timestamp"]


def test_read_logs_respects_limit(log_file):
    logger = _isolated_logger("test_logs_limit", log_file)

    for index in range(10):
        logger.info(f"message {index}")

    records = read_logs(limit=3)

    assert [record["message"] for record in records] == [
        "message 7",
        "message 8",
        "message 9",
    ]


def test_read_logs_skips_partial_lines(log_file):
    log_file.write_text(
        json.dumps({"level": "INFO", "message": "complete"}) + '\n{"level": "IN',
        encoding="utf-8",
    )

    assert read_logs() == [{"level": "INFO", "message": "complete"}]


def test_read_logs_without_file(log_file):
    assert read_logs() == []


def test_json_formatter_includes_traceback(log_file):
    logger = _isolated_logger("test_logs_traceback", log_file)

    try:
        raise ValueError("boom")
    except ValueError:
        logger.exception("failed")

    message = read_logs()[0]["message"]

    assert message.startswith("failed")
    assert "ValueError: boom" in message
