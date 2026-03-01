import json
import os
import re
import unicodedata
from datetime import datetime
from time import gmtime, strftime

import pytz


def _get_clean_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    # NOTE: Temporarily removing this for chinese songs
    # non_ascii = normalized.encode("ascii", "ignore").decode("ascii")
    non_symbols = re.compile(r"[^a-z0-9]+").sub("", normalized.casefold())

    return non_symbols


def _dump_results(file_name: str, data: dict) -> None:
    with open(f"{file_name}.json", "w") as file:
        json.dump(data, file, indent=4)


def _convert_seconds_to_readable_time(seconds: float | int) -> str:
    return strftime("%H:%M:%S", gmtime(seconds))


def _get_now() -> datetime:
    return datetime.now(pytz.timezone(os.getenv("TZ", "Asia/Singapore")))


def _format_time_with_locale(date: datetime) -> datetime:
    return date.astimezone(pytz.timezone(os.getenv("TZ", "Asia/Singapore")))


def _parse_cron_expression(cron_expression: str) -> dict:
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
