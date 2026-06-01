import logging
from typing import Any

import httpx
from fastapi import HTTPException, status

from lib.models.jellyfin import (
    JellyfinLibrary,
    JellyfinPlaylist,
    JellyfinTrack,
    JellyfinUser,
)
from lib.env import get_environment_variable


logger = logging.getLogger(__name__)


async def _jellyfin(
    path: str,
    *,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    json: dict[str, Any] | list[Any] | None = None,
    data: dict[str, Any] | str | bytes | None = None,
    timeout: float = 30.0,
) -> Any:
    """HTTP helper for the Jellyfin API."""

    api_key = get_environment_variable("JELLYFIN_API_KEY", ignore_error=False)
    api_url = get_environment_variable("JELLYFIN_URL", ignore_error=False)

    base_headers = {
        "X-Emby-Token": api_key,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.request(
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


async def get_jellyfin_users() -> list[JellyfinUser]:
    """Return all users registered in Jellyfin."""

    data = await _jellyfin("/Users")

    return [
        JellyfinUser(
            id=user.get("Id", ""),
            name=user.get("Name", ""),
        )
        for user in data
    ]


async def get_jellyfin_playlists(user_id: str) -> list[JellyfinPlaylist]:
    """Return all playlists visible to the given Jellyfin user."""

    response = await _jellyfin(
        f"/Users/{user_id}/Items",
        params={"IncludeItemTypes": "Playlist", "Recursive": True},
    )
    data = response.get("Items", [])

    return [
        JellyfinPlaylist(
            id=item["Id"],
            name=item["Name"],
            owner_id=item.get("UserId"),
        )
        for item in data
    ]


async def get_jellyfin_user_by_name(username: str) -> JellyfinUser | None:
    """Find a Jellyfin user by their username.

    Returns:
        JellyfinUser | None: The user object if found, otherwise None
    """

    jellyfin_users = await get_jellyfin_users()

    user = next((user for user in jellyfin_users if user.name == username), None)

    return user


async def search_jellyfin_track(
    artist_name: str, title: str, album: str, year: str
) -> list[JellyfinTrack]:
    """Search for audio tracks in Jellyfin matching the given metadata.

    Queries by artist and search term (title). Album and year filtering is
    currently disabled.

    Returns up to 10 results.
    """

    logger.info(
        f"Searching for track with artist='{artist_name}', title='{title}', album='{album}', year='{year}'"
    )

    response = await _jellyfin(
        "/Items",
        params={
            "includeItemTypes": "Audio",
            "recursive": "true",
            # "artists": artist_name,
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


async def create_jellyfin_playlist(
    playlist_name: str,
    user_id: str,
) -> dict[str, Any]:
    """Create a new private audio playlist in Jellyfin owned by user.

    Args:
        playlist_name: The name of the playlist to create
        user_id: The ID of the Jellyfin user who will own the playlist

    Returns:
        The created playlist data from Jellyfin
    """

    return await _jellyfin(
        "/Playlists",
        method="POST",
        json={
            "Name": playlist_name,
            "Ids": [],
            "UserId": user_id,
            "Users": [{"UserId": user_id, "CanEdit": True}],
            "MediaType": "Audio",
            "IsPublic": False,
        },
    )


async def add_songs_to_jellyfin_playlist(
    playlist_id: str,
    user_id: str,
    track_ids: list[str],
) -> dict[str, Any]:
    """Append tracks to an existing Jellyfin playlist."""

    return await _jellyfin(
        f"/Playlists/{playlist_id}/Items",
        method="POST",
        params={
            "playlistId": playlist_id,
            "userId": user_id,
            "ids": ",".join(track_ids),
        },
    )


async def get_or_create_jellyfin_playlist(
    playlist_name: str,
    username: str,
) -> tuple[str, str]:
    """Get an existing Jellyfin playlist by name or create a new one.

    Returns:
        tuple[str, str]: (playlist_id, user_id)

    Raises:
        HTTPException: If user is not found or playlist creation fails
    """

    jellyfin_user = await get_jellyfin_user_by_name(username=username)
    if not jellyfin_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to find username: {username}",
        )

    jellyfin_playlists = await get_jellyfin_playlists(user_id=jellyfin_user.id)

    existing_playlist = next(
        (
            playlist
            for playlist in jellyfin_playlists
            if playlist.name == playlist_name
            and (playlist.owner_id is None or playlist.owner_id == jellyfin_user.id)
        ),
        None,
    )
    existing_playlist_id = existing_playlist.id if existing_playlist else None

    if not existing_playlist_id:
        new_playlist = await create_jellyfin_playlist(
            playlist_name=playlist_name, user_id=jellyfin_user.id
        )
        existing_playlist_id = new_playlist.get("Id")

        if not existing_playlist_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create new playlist in Jellyfin",
            )

    return existing_playlist_id, jellyfin_user.id


async def delete_songs_from_jellyfin_playlist(
    playlist_id: str,
    track_ids: list[str],
) -> dict[str, Any]:
    """Remove tracks from a Jellyfin playlist by their playlist entry IDs."""

    return await _jellyfin(
        f"/Playlists/{playlist_id}/Items",
        method="DELETE",
        params={
            "entryIds": ",".join(track_ids),
        },
    )


async def get_jellyfin_playlist_songs(
    playlist_id: str, user_id: str
) -> list[JellyfinTrack]:
    """Return all tracks in a Jellyfin playlist."""

    response = await _jellyfin(
        f"/Playlists/{playlist_id}/Items", params={"userId": user_id}
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


async def update_jellyfin_playlist_image(
    playlist_id: str, image_url: str | None
) -> dict[str, Any] | None:
    """Set the primary cover image for a Jellyfin playlist from a remote URL.

    First attempts a remote-image download via Jellyfin's own endpoint.
    If that fails, the image bytes are then fetched directly and
    uploaded to Jellyfin.
    """
    if not image_url:
        return

    try:
        await _jellyfin(
            f"/Items/{playlist_id}/RemoteImages/Download",
            method="POST",
            params={"type": "Primary", "imageUrl": image_url},
        )
        return
    except httpx.HTTPStatusError as e:
        if not (e.response is not None and e.response.status_code == 400):
            logger.error("Failed to update playlist image with remote image")
    except httpx.RequestError as e:
        logger.error(f"Network error when setting remote playlist image: {e}")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        thumbnail_response = await client.get(image_url)
    thumbnail_response.raise_for_status()
    mime = thumbnail_response.headers.get("Content-Type") or (
        "image/png" if image_url.lower().endswith(".png") else "image/jpeg"
    )
    return await _jellyfin(
        f"/Items/{playlist_id}/Images/Primary",
        method="POST",
        headers={"Content-Type": mime},
        data=thumbnail_response.content,
    )


async def rescan_jellyfin_library() -> None:
    """Trigger a full metadata refresh on the configured download library."""

    media_folders_response = await _jellyfin("/Library/MediaFolders")

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

    await _jellyfin(
        f"/Items/{download_folder.get('Id')}/Refresh",
        method="POST",
        params={
            "recursive": "true",
            "imageRefreshMode": "None",
            "metadataRefreshMode": "FullRefresh",
            "replaceAllImages": "false",
            "regenerateTrickplay": "false",
            "replaceAllMetadata": "false",
        },
    )


async def is_jellyfin_scanning_library() -> bool:
    """Return True if the configured download library is currently being scanned."""

    download_library_name = get_environment_variable("DOWNLOAD_LIBRARY_NAME")

    for library in await get_jellyfin_libraries():
        if library.name == download_library_name and library.refresh_status == "Active":
            return True
    return False


async def get_jellyfin_libraries() -> list[JellyfinLibrary]:
    """Return all virtual folders (libraries) configured in Jellyfin."""

    response = await _jellyfin("/Library/VirtualFolders")
    return [
        JellyfinLibrary(
            name=folder.get("Name", ""),
            locations=folder.get("Locations", []),
            collection_type=folder.get("CollectionType", ""),
            item_id=folder.get("ItemId", ""),
            refresh_status=folder.get("RefreshStatus", ""),
        )
        for folder in response
    ]


async def create_jellyfin_download_library() -> None:
    """Create the download library in Jellyfin using DOWNLOAD_LIBRARY_NAME and DOWNLOAD_DIR."""

    library_name = get_environment_variable("DOWNLOAD_LIBRARY_NAME")
    download_dir = get_environment_variable("DOWNLOAD_DIR")

    await _jellyfin(
        "/Library/VirtualFolders",
        method="POST",
        params={
            "name": library_name,
            "path": download_dir,
            "collectionType": "music",
            "refreshLibrary": "true",
        },
        json={
            "LibraryOptions": {
                "Enabled": True,
                "EnableRealtimeMonitor": True,
                "EnableLUFSScan": False,
            }
        },
    )
    logger.info(f"Created Jellyfin library '{library_name}' at path '{download_dir}'")


async def ensure_download_library_exists() -> None:
    """Check whether the download library exists in Jellyfin and create it if not."""

    library_name = get_environment_variable("DOWNLOAD_LIBRARY_NAME")

    try:
        logger.info(f"Checking if Jellyfin library '{library_name}' exists")
        existing_names = {library.name for library in await get_jellyfin_libraries()}

        if library_name in existing_names:
            logger.info(f"Jellyfin library '{library_name}' already exists")
            return

        logger.info(f"Jellyfin library '{library_name}' not found, creating it")
        await create_jellyfin_download_library()
    except Exception as e:
        logger.warning(f"Failed to ensure Jellyfin download library exists: {e}")
