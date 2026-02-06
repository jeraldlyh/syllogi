import os
import requests


JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY")
JELLYFIN_BASE_URL = os.getenv("JELLYFIN_BASE_URL")


def _jellyfin(path: str, **params) -> dict:
    headers = {"X-Emby-Token": JELLYFIN_API_KEY}
    response = requests.get(
        f"{JELLYFIN_BASE_URL}{path}", headers=headers, params=params
    )
    response.raise_for_status()

    return response.json()


def get_jellyfin_artist(name: str) -> dict:
    return _jellyfin(f"/Artists/{name}")


def get_jellyfin_users() -> dict:
    return _jellyfin("/Users")
