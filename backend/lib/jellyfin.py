import logging
from typing import Any

import requests
from fastapi import HTTPException, status

from lib.common import JellyfinPlaylist, JellyfinTrack, JellyfinUser
from lib.env import get_environment_variable


logger = logging.getLogger(__name__)


def _jellyfin(
    path: str,
    *,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    json: dict[str, Any] | list[Any] | None = None,
    data: dict[str, Any] | str | bytes | None = None,
    timeout: float = 30.0,
) -> Any:
    api_key = get_environment_variable("JELLYFIN_API_KEY", ignore_error=False)
    api_url = get_environment_variable("JELLYFIN_URL", ignore_error=False)

    base_headers = {
        "X-Emby-Token": api_key,
        "Content-Type": "application/json",
    }

    response = requests.request(
        method=method.upper(),
        url=f"{api_url}{path}",
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


def get_jellyfin_users() -> list[JellyfinUser]:
    data = _jellyfin("/Users")

    return [
        JellyfinUser(
            id=user.get("Id", ""),
            name=user.get("Name", ""),
        )
        for user in data
    ]


def get_jellyfin_playlists(user_id: str) -> list[JellyfinPlaylist]:
    response = _jellyfin(
        f"/Users/{user_id}/Items",
        params={"IncludeItemTypes": "Playlist", "Recursive": True},
    )
    data = response.get("Items", [])

    return [
        JellyfinPlaylist(
            id=item["Id"],
            name=item["Name"],
        )
        for item in data
    ]


def get_jellyfin_user_by_name(username: str) -> JellyfinUser:
    jellyfin_users = get_jellyfin_users()

    user = next(user for user in jellyfin_users if user.name == username)

    return user


def search_jellyfin_track(
    artist_name: str, title: str, album: str, year: str
) -> list[JellyfinTrack]:
    logger.info(
        f"Searching for track with artist='{artist_name}', title='{title}', album='{album}', year='{year}'"
    )

    response = _jellyfin(
        "/Items",
        params={
            "includeItemTypes": "Audio",
            "recursive": "true",
            "artists": artist_name,
            "searchTerm": title,
            # "album": album,
            "fields": "Path,Album,Artists,CumulativeRunTimeTicks",
            # "years": year,
            "limit": 10,
            "enableTotalRecordCount": "false",
            "enableImages": "false",
        },
    )
    data = response.get("Items", [])

    return [
        JellyfinTrack(
            id=item.get("Id", ""),
            track_name=item.get("Name", ""),
            album_name=item.get("Album", ""),
            album_id=item.get("AlbumId", ""),
            musicbrainz_id=item.get("ProviderIds", {}).get("MusicBrainzRecording", ""),
            artists=item.get("Artists", []),
            duration_ticks=item.get("CumulativeRunTimeTicks", 0),
            year=str(item.get("ProductionYear", "")),
        )
        for item in data
    ]


def create_jellyfin_playlist(
    playlist_name: str,
    user_id: str,
) -> dict[str, Any]:
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


def add_songs_to_jellyfin_playlist(
    playlist_id: str,
    user_id: str,
    track_ids: list[str],
) -> dict[str, Any]:
    return _jellyfin(
        f"/Playlists/{playlist_id}/Items",
        method="POST",
        params={
            "playlistId": playlist_id,
            "userId": user_id,
            "ids": ",".join(track_ids),
        },
    )


def delete_songs_from_jellyfin_playlist(
    playlist_id: str,
    track_ids: list[str],
) -> dict[str, Any]:
    return _jellyfin(
        f"/Playlists/{playlist_id}/Items",
        method="DELETE",
        params={
            "entryIds": ",".join(track_ids),
        },
    )


def get_jellyfin_playlist_songs(playlist_id: str, user_id: str) -> list[JellyfinTrack]:
    response = _jellyfin(f"/Playlists/{playlist_id}/Items", params={"userId": user_id})
    data = response.get("Items", [])

    return [
        JellyfinTrack(
            id=item.get("Id", ""),
            track_name=item.get("Name", ""),
            album_name=item.get("Album", ""),
            album_id=item.get("AlbumId", ""),
            musicbrainz_id=item.get("ProviderIds", {}).get("MusicBrainzRecording", ""),
            artists=item.get("Artists", []),
            duration_ticks=item.get("CumulativeRunTimeTicks", 0),
            year=str(item.get("ProductionYear", "")),
        )
        for item in data
    ]


def update_jellyfin_playlist_image(
    playlist_id: str, image_url: str | None
) -> dict[str, Any] | None:
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
            logger.error("Failed to update playlist image with remote image")

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


def rescan_jellyfin_library() -> None:
    media_folders_response = _jellyfin("/Library/MediaFolders")

    download_library_name = get_environment_variable("DOWNLOAD_LIBRARY_NAME")
    download_folder = next(
        (
            folder
            for folder in media_folders_response.get("Items", [])
            if folder.get("Name") == download_library_name
        ),
        None,
    )

    if download_folder is None:
        logger.warning(
            f"Could not find media folder with name '{download_library_name}' to rescan"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Media folder not found",
        )

    _jellyfin(
        f"/Items/{download_folder.get('Id')}/Refresh",
        method="POST",
        params={
            "Recursive": "true",
            "ImageRefreshMode": "Default",
            "MetadataRefreshMode": "Default",
            "ReplaceAllImages": "false",
            "RegenerateTrickplay": "false",
            "ReplaceAllMetadata": "false",
        },
    )


def is_jellyfin_scanning_library() -> bool:
    response = _jellyfin("/Library/VirtualFolders")

    for folder in response:
        if (
            folder.get("Name") == get_environment_variable("DOWNLOAD_LIBRARY_NAME")
            and folder.get("RefreshStatus", "") == "Active"
        ):
            return True
    return False
