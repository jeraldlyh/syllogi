import json
import os
import re
import unicodedata
from datetime import datetime
from time import gmtime, strftime

import pytz

# DEBUG_DIRECTORY = Path(__file__).resolve().parent.parent / "debug"
DEBUG_DIRECTORY = "debug"


def _get_clean_name(name: str) -> str:
    """Clean a name by removing accents, special characters, and normalizing case."""

    normalized = unicodedata.normalize("NFKD", name)
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    lower = stripped.casefold()
    cleaned = re.compile(r"[^\w]+").sub("", lower)
    cleaned = cleaned.replace("_", "")

    return cleaned


def _dump_results(file_name: str, data: dict) -> None:
    """Dump results to a JSON file for debugging purposes."""

    if not os.path.exists(DEBUG_DIRECTORY):
        os.makedirs(DEBUG_DIRECTORY)

    sanitized_file_name = re.sub(r"[^\w\-]", "_", file_name)
    debug_path = os.path.join(DEBUG_DIRECTORY, f"{sanitized_file_name}.json")
    with open(debug_path, "w") as file:
        json.dump(data, file, indent=4)


def _convert_seconds_to_readable_time(seconds: float | int) -> str:
    """Convert seconds to a human-readable format (HH:MM:SS)."""

    return strftime("%H:%M:%S", gmtime(seconds))


def _get_now() -> datetime:
    """Get the current time in the specified timezone."""

    return datetime.now(pytz.timezone(os.getenv("TZ", "Asia/Singapore")))


def _format_time_with_locale(date: datetime) -> datetime:
    """Format a datetime object to the specified timezone."""

    return date.astimezone(pytz.timezone(os.getenv("TZ", "Asia/Singapore")))


def _parse_cron_expression(cron_expression: str) -> dict:
    """Parse a cron expression into its components."""

    parts = cron_expression.split()

    if len(parts) != 5:
        raise ValueError("Invalid cron expression. Expected 5 parts.")

    return {
        "minute": parts[0],
        "hour": parts[1],
        "day": parts[2],
        "month": parts[3],
        "day_of_week": parts[4],
    }
