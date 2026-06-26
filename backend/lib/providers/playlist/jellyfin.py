import asyncio
import logging
from typing import Any

import httpx

from lib.env import get_environment_variable
from lib.providers.base import MusicPlaylistProvider
from lib.utils import sanitize_filename
from lib.models.provider import (
    ProviderError,
    ProviderPlaylist,
    ProviderTrack,
    ProviderUser,
)
from lib.models.jellyfin import JellyfinLibrary

logger = logging.getLogger(__name__)


class JellyfinProvider(MusicPlaylistProvider):
    """Music provider implementation for Jellyfin."""

    async def _jellyfin(
        self,
        path: str,
        *,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        json: dict[str, Any] | list[Any] | None = None,
        data: dict[str, Any] | str | bytes | None = None,
        timeout: float = 30.0,
    ) -> Any:
        """HTTP helper for the Jellyfin API.

        Raises:
            ProviderError: If required environment variables are missing.
        """

        api_key = get_environment_variable("JELLYFIN_API_KEY", ignore_error=False)
        url = get_environment_variable("JELLYFIN_URL", ignore_error=False)

        if not api_key or not url:
            raise ProviderError("Jellyfin API key and URL must be configured")

        base_headers = {
            "X-Emby-Token": api_key,
            "Content-Type": "application/json",
        }
        request_url = f"{str(url).rstrip('/')}{path}"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method.upper(),
                url=request_url,
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

    async def get_users(self) -> list[ProviderUser]:
        """Return all users registered in Jellyfin."""

        data = await self._jellyfin("/Users")

        return [
            ProviderUser(
                id=user.get("Id", ""),
                name=user.get("Name", ""),
            )
            for user in data
        ]

    async def get_user_by_name(self, username: str) -> ProviderUser | None:
        """Find a Jellyfin user by their username."""

        users = await self.get_users()
        return next((user for user in users if user.name == username), None)

    async def get_playlists(
        self,
        *,
        user_id: str,
        username: str = "",
        password: str = "",
    ) -> list[ProviderPlaylist]:
        """Return all playlists visible to the given Jellyfin user."""

        response = await self._jellyfin(
            f"/Users/{user_id}/Items",
            params={"IncludeItemTypes": "Playlist", "Recursive": True},
        )
        data = response.get("Items", [])
        return [
            ProviderPlaylist(
                id=item["Id"],
                name=item["Name"],
                owner_id=item.get("UserId"),
            )
            for item in data
        ]

    async def get_or_create_playlist(
        self,
        *,
        playlist_name: str,
        username: str,
        is_public: bool = False,
        password: str = "",
    ) -> tuple[str, str]:
        """Get an existing Jellyfin playlist by name or create a new one.

        Returns:
            tuple[str, str]: (playlist_id, user_id)

        Raises:
            ProviderError: If user is not found or playlist creation fails
        """

        user = await self.get_user_by_name(username=username)

        if not user:
            raise ProviderError(f"Unable to find username: {username}")

        playlists = await self.get_playlists(user_id=user.id)

        existing_playlist = next(
            (
                playlist
                for playlist in playlists
                if playlist.name == playlist_name
                and (playlist.owner_id is None or playlist.owner_id == user.id)
            ),
            None,
        )
        playlist_id = existing_playlist.id if existing_playlist else None

        if not playlist_id:
            new_playlist = await self.create_playlist(
                playlist_name=playlist_name,
                user_id=user.id,
                is_public=is_public,
            )
            playlist_id = new_playlist.id

            if not playlist_id:
                raise ProviderError("Unable to create new playlist in Jellyfin")

        return playlist_id, user.id

    async def create_playlist(
        self,
        *,
        playlist_name: str,
        user_id: str,
        is_public: bool = False,
        username: str = "",
        password: str = "",
    ) -> ProviderPlaylist:
        """Create a new audio playlist in Jellyfin owned by user."""

        data = await self._jellyfin(
            "/Playlists",
            method="POST",
            json={
                "Name": playlist_name,
                "Ids": [],
                "UserId": user_id,
                "Users": [{"UserId": user_id, "CanEdit": True}],
                "MediaType": "Audio",
                "IsPublic": is_public,
            },
        )

        return ProviderPlaylist(
            id=data.get("Id", ""),
            name=playlist_name,
            owner_id=user_id,
        )

    async def delete_playlist(
        self,
        *,
        playlist_id: str,
        username: str = "",
        password: str = "",
    ) -> None:
        """Delete a Jellyfin playlist by its ID."""

        await self._jellyfin(f"/Items/{playlist_id}", method="DELETE")

    async def get_playlist_songs(
        self,
        *,
        playlist_id: str,
        user_id: str,
        username: str = "",
        password: str = "",
    ) -> list[ProviderTrack]:
        """Return all tracks in a Jellyfin playlist."""

        response = await self._jellyfin(
            f"/Playlists/{playlist_id}/Items", params={"userId": user_id}
        )
        data = response.get("Items", [])

        return [
            ProviderTrack(
                id=item.get("Id", ""),
                track_name=item.get("Name", ""),
                album_name=item.get("Album", ""),
                album_id=item.get("AlbumId", ""),
                musicbrainz_id=item.get("ProviderIds", {}).get(
                    "MusicBrainzRecording", ""
                ),
                artists=item.get("Artists", []),
                duration_ticks=item.get("CumulativeRunTimeTicks", 0),
                year=str(item.get("ProductionYear", "")),
            )
            for item in data
        ]

    async def add_songs_to_playlist(
        self,
        *,
        playlist_id: str,
        user_id: str,
        track_ids: list[str],
        username: str = "",
        password: str = "",
        batch_size: int = 50,
    ) -> None:
        """Append tracks to an existing Jellyfin playlist.

        Splits requests into batches to avoid HTTP 414 Request-URI Too Large
        errors when there are many tracks.
        """

        for i in range(0, len(track_ids), batch_size):
            batch = track_ids[i : i + batch_size]

            await self._jellyfin(
                f"/Playlists/{playlist_id}/Items",
                method="POST",
                params={
                    "playlistId": playlist_id,
                    "userId": user_id,
                    "ids": ",".join(batch),
                },
            )

    async def delete_songs_from_playlist(
        self,
        *,
        playlist_id: str,
        entry_ids: list[str],
        username: str = "",
        password: str = "",
    ) -> None:
        """Remove tracks from a Jellyfin playlist by their playlist entry IDs."""

        await self._jellyfin(
            f"/Playlists/{playlist_id}/Items",
            method="DELETE",
            params={
                "entryIds": ",".join(entry_ids),
            },
        )

    async def search_track(
        self, *, artist_name: str, title: str, album: str, year: str
    ) -> list[ProviderTrack]:
        """Search for audio tracks in Jellyfin matching the given metadata.

        Queries by artist and search term (title). Album and year filtering is
        currently disabled.

        Returns up to 10 results.
        """

        logger.info(
            f"Searching for track with artist='{artist_name}', title='{title}', "
            f"album='{album}', year='{year}'"
        )

        response = await self._jellyfin(
            "/Items",
            params={
                "includeItemTypes": "Audio",
                "recursive": "true",
                "searchTerm": sanitize_filename(title),
                "fields": "Path,Album,Artists,CumulativeRunTimeTicks",
                "limit": 10,
                "enableTotalRecordCount": "false",
                "enableImages": "false",
            },
        )
        data = response.get("Items", [])

        return [
            ProviderTrack(
                id=item.get("Id", ""),
                track_name=item.get("Name", ""),
                album_name=item.get("Album", ""),
                album_id=item.get("AlbumId", ""),
                musicbrainz_id=item.get("ProviderIds", {}).get(
                    "MusicBrainzRecording", ""
                ),
                artists=item.get("Artists", []),
                duration_ticks=item.get("CumulativeRunTimeTicks", 0),
                year=str(item.get("ProductionYear", "")),
            )
            for item in data
        ]

    async def update_playlist_image(
        self, *, playlist_id: str, image_url: str | None
    ) -> None:
        """Set the primary cover image for a Jellyfin playlist from a remote URL.

        First attempts a remote-image download via Jellyfin's own endpoint.
        If that fails, the image bytes are then fetched directly and
        uploaded to Jellyfin.
        """

        if not image_url:
            return

        try:
            await self._jellyfin(
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

        await self._jellyfin(
            f"/Items/{playlist_id}/Images/Primary",
            method="POST",
            headers={"Content-Type": mime},
            data=thumbnail_response.content,
        )

    async def update_playlist_visibility(
        self,
        *,
        playlist_name: str,
        username: str,
        is_public: bool,
        password: str = "",
    ) -> None:
        """Update the visibility of an existing Jellyfin playlist by
        recreating it with all existing tracks preserved.

        Unable to directly update the visibility of a playlist via the API due to
        the following issue: https://github.com/jellyfin/jellyfin/issues/13476

        This is a Jellyfin-specific method not on the base MusicProvider interface.
        """

        user = await self.get_user_by_name(username=username)

        if not user:
            logger.warning(
                f"Unable to find Jellyfin user '{username}' when updating playlist visibility"
            )
            return

        playlists = await self.get_playlists(user_id=user.id)

        existing_playlist = next(
            (
                playlist
                for playlist in playlists
                if playlist.name == playlist_name
                and (playlist.owner_id is None or playlist.owner_id == user.id)
            ),
            None,
        )

        if not existing_playlist:
            logger.warning(
                f"Unable to find existing Jellyfin playlist '{playlist_name}' "
                f"for user '{username}' when updating playlist visibility"
            )
            return

        existing_tracks = await self.get_playlist_songs(
            playlist_id=existing_playlist.id,
            user_id=user.id,
        )
        track_ids = [track.id for track in existing_tracks]

        await self.delete_playlist(playlist_id=existing_playlist.id)

        new_playlist = await self.create_playlist(
            playlist_name=playlist_name,
            user_id=user.id,
            is_public=is_public,
        )

        if not new_playlist.id:
            logger.error(
                f"Failed to recreate Jellyfin playlist '{playlist_name}' when updating visibility"
            )
            return

        if track_ids:
            await self.add_songs_to_playlist(
                playlist_id=new_playlist.id,
                user_id=user.id,
                track_ids=track_ids,
            )

    async def rescan_library(self) -> None:
        """Trigger a full metadata refresh on the configured download library."""

        media_folders_response = await self._jellyfin("/Library/MediaFolders")

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
            raise ProviderError("Media folder not found")

        await self._jellyfin(
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

    async def is_scanning_library(self) -> bool:
        """Return True if the configured download library is currently being scanned."""

        download_library_name = get_environment_variable("DOWNLOAD_LIBRARY_NAME")
        libraries = await self._get_libraries()

        return any(
            library.name == download_library_name and library.refresh_status == "Active"
            for library in libraries
        )

    async def _get_libraries(self) -> list[JellyfinLibrary]:
        """Return all virtual folders (libraries) configured in Jellyfin."""

        response = await self._jellyfin("/Library/VirtualFolders")

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

    async def wait_for_rescan(
        self,
        *,
        poll_interval_seconds: int = 15,
        max_wait_seconds: int = 600,
    ) -> None:
        """Trigger a rescan and block until the scan finishes."""

        await self.rescan_library()

        waited = 0

        while waited < max_wait_seconds:
            if not await self.is_scanning_library():
                logger.info("Jellyfin library scan complete")
                return
            await asyncio.sleep(poll_interval_seconds)
            waited += poll_interval_seconds

        logger.warning(
            f"Jellyfin library scan did not complete within {max_wait_seconds}s"
        )

    async def _create_download_library(self) -> None:
        """Create the download library in Jellyfin using DOWNLOAD_LIBRARY_NAME and DOWNLOAD_DIR."""

        library_name = get_environment_variable("DOWNLOAD_LIBRARY_NAME")
        download_dir = get_environment_variable("DOWNLOAD_DIR")

        await self._jellyfin(
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
        logger.info(
            f"Created Jellyfin library '{library_name}' at path '{download_dir}'"
        )

    async def ensure_download_library_exists(self) -> None:
        """Check whether the download library exists in Jellyfin and create it if not."""

        library_name = get_environment_variable("DOWNLOAD_LIBRARY_NAME")

        logger.info(f"Checking if Jellyfin library '{library_name}' exists")

        libraries = await self._get_libraries()
        existing_names = {library.name for library in libraries}

        if library_name in existing_names:
            logger.info(f"Jellyfin library '{library_name}' already exists")
            return

        logger.info(f"Jellyfin library '{library_name}' not found, creating it")
        await self._create_download_library()
