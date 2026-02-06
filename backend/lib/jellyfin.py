import os
import requests

from flask import jsonify

JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY")
JELLYFIN_BASE_URL = os.getenv("JELLYFIN_BASE_URL")


def _jellyfin(
    path: str,
    *,
    method: str = "GET",
    params: dict | None = None,
    json: dict | list | None = None,
    data: dict | str | bytes | None = None,
    timeout: float = 30.0,
) -> dict:
    headers = {"X-Emby-Token": JELLYFIN_API_KEY, "Content-Type": "application/json"}
    response = requests.request(
        method.upper(),
        f"{JELLYFIN_BASE_URL}{path}",
        headers=headers,
        params=params,
        json=json,
        data=data,
        timeout=timeout,
    )
    response.raise_for_status()

    return response.json()


def _get_jellyfin_artist(name: str) -> dict:
    return _jellyfin(f"/Artists/{name}")


def _get_jellyfin_users() -> dict:
    return _jellyfin("/Users")


def _get_jellyfin_playlists(user_id: str) -> dict:
    return _jellyfin(
        f"/Users/{user_id}/Items",
        params={"IncludeItemTypes": "Playlist", "Recursive": True},
    )


def _get_jellyfin_user_by_name(username: str) -> dict:
    jellyfin_users = _get_jellyfin_users()

    user = next(user for user in jellyfin_users if user.get("Name") == username)

    if not user:
        return jsonify({"error": f"Unable to find user: {username}"}), 400
    return user


def _create_jellyfin_playlist(
    playlist_name: str,
    user_id: str,
) -> None:
    return _jellyfin(
        "/Playlists",
        method="POST",
        json={
            "Name": playlist_name,
            "Ids": [],
            "UserId": user_id,
            "Users": [{"UserId": user_id, "CanEdit": True}],
            "MediaType": "Audio",
            "IsPublic": True,
        },
    )
