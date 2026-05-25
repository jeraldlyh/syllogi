import glob
import json
import logging
import os
from pathlib import Path
import re
import unicodedata
from datetime import datetime
from time import gmtime, strftime

import pytz

from lib.env import get_environment_variable

DEBUG_DIRECTORY = "debug"

logger = logging.getLogger(__name__)


def get_clean_name(name: str) -> str:
    """Clean a name by removing accents, special characters, and normalizing case."""

    normalized = unicodedata.normalize("NFKC", name)
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    lower = stripped.casefold()
    cleaned = re.compile(r"[^\w]+").sub("", lower)
    cleaned = cleaned.replace("_", "")

    return cleaned


def dump_results(file_name: str, data: dict) -> None:
    """Dump results to a JSON file for debugging purposes."""

    if not os.path.exists(DEBUG_DIRECTORY):
        os.makedirs(DEBUG_DIRECTORY)

    sanitized_file_name = re.sub(r"[^\w\-]", "_", file_name)
    debug_path = os.path.join(DEBUG_DIRECTORY, f"{sanitized_file_name}.json")
    with open(debug_path, "w") as file:
        json.dump(data, file, indent=4)


def convert_seconds_to_readable_time(seconds: float | int) -> str:
    """Convert seconds to a human-readable format (HH:MM:SS)."""

    return strftime("%H:%M:%S", gmtime(seconds))


def get_now() -> datetime:
    """Get the current time in the specified timezone."""

    return datetime.now(pytz.timezone(os.getenv("TZ", "Asia/Singapore")))


def format_time_with_locale(date: datetime) -> datetime:
    """Format a datetime object to the specified timezone."""

    return date.astimezone(pytz.timezone(os.getenv("TZ", "Asia/Singapore")))


def parse_cron_expression(cron_expression: str) -> dict:
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


def sanitize_filename(name: str) -> str:
    """Sanitize a filename by removing or replacing characters that are not allowed in file names."""

    illegal_chars = '\\/:*?"<>|'
    return "".join(
        char
        for char in unicodedata.normalize("NFKC", name)
        if char not in illegal_chars
    ).strip()


def get_download_path(artist_name: str, track_name: str, album_name: str = "") -> str:
    """Get the directory path where a song should be downloaded based on artist and album."""
    sanitized_artist_name = sanitize_filename(artist_name)
    sanitized_track_name = sanitize_filename(track_name)

    download_dir = str(get_environment_variable("DOWNLOAD_DIR"))

    if album_name:
        sanitized_album_name = sanitize_filename(album_name)
        return f"{Path(download_dir)}/{sanitized_artist_name}/{sanitized_album_name}/{sanitized_track_name}"
    return (
        f"{Path(download_dir)}/{sanitized_artist_name}/Singles/{sanitized_track_name}"
    )


def is_track_exists(artist_name: str, track_name: str, album_name: str = "") -> bool:
    download_path = get_download_path(artist_name, track_name, album_name)
    existing_paths = glob.glob(f"{glob.escape(download_path)}.*")

    return bool(existing_paths)


def normalize(text: str) -> str:
    """Normalize text for Unicode-aware, case-insensitive comparison."""

    return unicodedata.normalize("NFKC", text).casefold().strip()
