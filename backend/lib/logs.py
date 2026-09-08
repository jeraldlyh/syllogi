import json
import logging
import os
import tempfile
from collections import deque
from datetime import UTC, datetime

LOG_MAX_BYTES = 5_000_000
LOG_BACKUP_COUNT = 3


def _resolve_log_file() -> str:
    """Resolve the log file path, falling back to a temporary directory if it is not writable."""
    log_dir = os.getenv("LOG_DIR", "/logs")

    try:
        os.makedirs(log_dir, exist_ok=True)
    except OSError:
        log_dir = tempfile.gettempdir()
    return os.path.join(log_dir, "syllogi.log")


LOG_FILE = _resolve_log_file()


class JsonFormatter(logging.Formatter):
    """Formatter that writes each record as a JSON line for the dashboard to read back."""

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
                "level": record.levelname,
                "module": record.module,
                "message": super().format(record),
            }
        )


def read_logs(limit: int = 500) -> list[dict[str, str]]:
    """Read the most recent log records from the log file."""
    log_file = _resolve_log_file()

    if not os.path.exists(log_file):
        return []

    with open(log_file, encoding="utf-8", errors="replace") as file:
        lines = deque(file, maxlen=limit)

    records: list[dict[str, str]] = []

    for line in lines:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records
