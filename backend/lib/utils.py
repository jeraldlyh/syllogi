import re
import json
import unicodedata
from time import gmtime, strftime


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
