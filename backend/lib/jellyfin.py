import os
import requests

from flask import jsonify, current_app
from typing import List

JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY")
JELLYFIN_BASE_URL = os.getenv("JELLYFIN_BASE_URL")


def _jellyfin(
    path: str,
    *,
    method: str = "GET",
    params: dict | None = None,
    headers: dict | None = None,
    json: dict | list | None = None,
    data: dict | str | bytes | None = None,
    timeout: float = 30.0,
) -> dict | None:
    base_headers = {
        "X-Emby-Token": JELLYFIN_API_KEY,
        "Content-Type": "application/json",
    }

    response = requests.request(
        method.upper(),
        f"{JELLYFIN_BASE_URL}{path}",
        headers={**base_headers, **(headers or {})},
        params=params,
        json=json,
        data=data,
        timeout=timeout,
    )
    response.raise_for_status()

    if response.status_code == 204 or not response.content:
        return None
    return response.json()


def _get_jellyfin_artist(name: str) -> dict:
    return _jellyfin(f"/Artists/{name}")


def _get_jellyfin_users() -> dict:
    return _jellyfin("/Users")


def _get_jellyfin_playlists(user_id: str) -> List[dict]:
    response = _jellyfin(
        f"/Users/{user_id}/Items",
        params={"IncludeItemTypes": "Playlist", "Recursive": True},
    )
    return response.get("Items")


def _get_jellyfin_user_by_name(username: str) -> dict:
    jellyfin_users = _get_jellyfin_users()

    user = next(user for user in jellyfin_users if user.get("Name") == username)

    if not user:
        return jsonify({"error": f"Unable to find user: {username}"}), 400
    return user


def _search_jellyfin_songs(artist_name: str, title: str) -> List[dict]:
    response = _jellyfin(
        "/Items",
        params={
            "includeItemTypes": "Audio",
            "recursive": "true",
            "artists": artist_name,
            "searchTerm": title,
            "Fields": "ProviderIds,Path,Album,Artists",
            "limit": 10,
            "enableTotalRecordCount": "false",
            "enableImages": "false",
        },
    )
    return response.get("Items")


def _create_jellyfin_playlist(
    playlist_name: str,
    user_id: str,
) -> dict:
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


def _add_songs_to_jellyfin_playlist(
    playlist_id: str,
    user_id: str,
    track_ids: List[str],
) -> dict:
    return _jellyfin(
        f"/Playlists/{playlist_id}/Items",
        method="POST",
        params={
            "playlistId": playlist_id,
            "userId": user_id,
            "ids": ",".join(track_ids),
        },
    )


def _delete_songs_from_jellyfin_playlist(
    playlist_id: str,
    track_ids: List[str],
) -> dict:
    return _jellyfin(
        f"/Playlists/{playlist_id}/Items",
        method="DELETE",
        params={
            "entryIds": ",".join(track_ids),
        },
    )


def _get_jellyfin_playlist_songs(playlist_id: str, user_id: str) -> List[dict]:
    response = _jellyfin(f"/Playlists/{playlist_id}/Items", params={"userId": user_id})
    return response.get("Items")


def _update_jellyfin_playlist_image(playlist_id: str, image_url: str | None) -> dict:
    if not image_url:
        return

    try:
        _jellyfin(
            f"/Items/{playlist_id}/RemoteImages/Download",
            method="POST",
            params={"type": "Primary", "imageUrl": image_url},
        )
    except requests.HTTPError as e:
        if not (e.response is not None and e.response.status_code == 400):
            current_app.logger.error(
                "Failed to update playlist image with remote image"
            )

    thumbnail_response = requests.get(image_url)
    thumbnail_response.raise_for_status()
    mime = thumbnail_response.headers.get("Content-Type") or (
        "image/png" if image_url.lower().endswith(".png") else "image/jpeg"
    )
    return _jellyfin(
        f"/Items/{playlist_id}/Images/Primary",
        method="POST",
        headers={"Content-Type": mime},
        data=thumbnail_response.content,
    )
