import asyncio
import hashlib
import logging
import secrets
from typing import Any

import httpx

from lib.env import get_environment_variable
from lib.providers.base import MusicPlaylistProvider
from lib.models.provider import (
    ProviderError,
    ProviderPlaylist,
    ProviderTrack,
    ProviderUser,
)

logger = logging.getLogger(__name__)


class NavidromeProvider(MusicPlaylistProvider):
    """Navidrome music server provider using the Subsonic REST API v1.16.1."""

    async def _subsonic(
        self,
        method: str,
        *,
        params: dict[str, Any] | None = None,
        http_method: str = "GET",
        timeout: float = 30.0,
    ) -> Any:
        """HTTP helper for the Subsonic API.

        Raises:
            ProviderError: If required environment variables are missing.
        """
        url = str(get_environment_variable("NAVIDROME_URL", ignore_error=False))
        username = str(
            get_environment_variable("NAVIDROME_USERNAME", ignore_error=False)
        )
        password = str(
            get_environment_variable("NAVIDROME_PASSWORD", ignore_error=False)
        )

        if not url or not username or not password:
            raise ProviderError(
                "Navidrome URL, username, and password must be configured"
            )

        salt = secrets.token_urlsafe(8)
        token = hashlib.md5((password + salt).encode("utf-8")).hexdigest()

        base_params: dict[str, Any] = {
            "u": username,
            "t": token,
            "s": salt,
            "v": "1.16.1",
            "c": "syllogi",
            "f": "json",
        }

        if params:
            base_params.update(params)

        request_url = f"{url.rstrip('/')}/rest/{method}"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=http_method.upper(),
                url=request_url,
                params=base_params,
                timeout=timeout,
            )

        response.raise_for_status()
        body = response.json()

        subsonic_response = body.get("subsonic-response", {})
        status = subsonic_response.get("status")

        if status != "ok":
            return {}
        return {
            k: v for k, v in subsonic_response.items() if k not in ("status", "version")
        }

    async def get_users(self) -> list[ProviderUser]:
        """Return all users registered in Navidrome."""

        data = await self._subsonic("getUsers")
        users = data.get("users", {}).get("user", [])

        if isinstance(users, dict):
            users = [users]

        return [
            ProviderUser(id=str(user.get("id")), name=user.get("username", ""))
            for user in users
        ]

    async def get_user_by_name(self, username: str) -> ProviderUser | None:
        """Find a Navidrome user by their username."""

        data = await self._subsonic("getUser", params={"username": username})
        user = data.get("user", {})

        return ProviderUser(
            id=str(user.get("id", "")),
            name=user.get("username", ""),
        )

    async def get_playlists(self, user_id: str) -> list[ProviderPlaylist]:
        """Return all playlists visible to the given Navidrome user."""

        data = await self._subsonic("getPlaylists")
        playlists = data.get("playlists", {}).get("playlist", [])

        if isinstance(playlists, dict):
            playlists = [playlists]

        return [
            ProviderPlaylist(
                id=playlist.get("id", ""),
                name=playlist.get("name", ""),
                owner_id=playlist.get("owner"),
            )
            for playlist in playlists
        ]

    async def get_or_create_playlist(
        self, playlist_name: str, username: str, is_public: bool = False
    ) -> tuple[str, str]:
        """Get an existing Navidrome playlist by name or create a new one.

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
                pl
                for pl in playlists
                if pl.name == playlist_name
                and (pl.owner_id is None or pl.owner_id == username)
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
                raise ProviderError("Unable to create new playlist in Navidrome")

        return playlist_id, user.id

    async def create_playlist(
        self, playlist_name: str, user_id: str, is_public: bool = False
    ) -> ProviderPlaylist:
        """Create a new playlist in Navidrome."""

        data = await self._subsonic(
            "createPlaylist",
            params={"name": playlist_name},
            http_method="POST",
        )

        playlist = data.get("playlist", {})

        return ProviderPlaylist(
            id=playlist.get("id", ""),
            name=playlist.get("name", playlist_name),
            owner_id=playlist.get("owner"),
        )

    async def delete_playlist(self, playlist_id: str) -> None:
        """Delete a Navidrome playlist by its ID."""

        await self._subsonic(
            "deletePlaylist",
            params={"id": playlist_id},
            http_method="POST",
        )

    async def get_playlist_songs(
        self, playlist_id: str, user_id: str
    ) -> list[ProviderTrack]:
        """Return all tracks in a Navidrome playlist."""

        data = await self._subsonic("getPlaylist", params={"id": playlist_id})
        playlist = data.get("playlist", {})
        entries = playlist.get("entry", [])

        if isinstance(entries, dict):
            entries = [entries]

        return [
            ProviderTrack(
                id=entry.get("id", ""),
                track_name=entry.get("title", ""),
                album_name=entry.get("album", ""),
                album_id=entry.get("albumId", ""),
                musicbrainz_id="",  # TODO: check if plugins provide MusicBrainz ID in the response
                artists=([entry["artist"]] if entry.get("artist") else []),
                duration_ticks=int(entry.get("duration", 0)) * 10_000_000,
                year=str(entry.get("year", "")),
            )
            for entry in entries
        ]

    async def add_songs_to_playlist(
        self, playlist_id: str, user_id: str, track_ids: list[str]
    ) -> None:
        """Append tracks to an existing Navidrome playlist."""

        await self._subsonic(
            "updatePlaylist",
            params={
                "playlistId": playlist_id,
                "songIdToAdd": track_ids,
            },
            http_method="POST",
        )

    async def delete_songs_from_playlist(
        self, playlist_id: str, entry_ids: list[str]
    ) -> None:
        """Remove tracks from a Navidrome playlist by their 0-based indices."""

        await self._subsonic(
            "updatePlaylist",
            params={
                "playlistId": playlist_id,
                "songIndexToRemove": entry_ids,
            },
            http_method="POST",
        )

    async def search_track(
        self, artist_name: str, title: str, album: str, year: str
    ) -> list[ProviderTrack]:
        """Search for tracks in Navidrome matching the given metadata."""

        logger.info(
            f"Searching for track with artist='{artist_name}', title='{title}', album='{album}', year='{year}'",
        )

        query = f"{artist_name} {title}".strip()
        data = await self._subsonic(
            "search3",
            params={"query": query, "songCount": "10"},
        )

        result = data.get("searchResult3", {})
        songs = result.get("song", [])

        if isinstance(songs, dict):
            songs = [songs]

        return [
            ProviderTrack(
                id=song.get("id", ""),
                track_name=song.get("title", ""),
                album_name=song.get("album", ""),
                album_id=song.get("albumId", ""),
                musicbrainz_id="",  # TODO: check if plugins provide MusicBrainz ID in the response
                artists=([song["artist"]] if song.get("artist") else []),
                duration_ticks=int(song.get("duration", 0)) * 10_000_000,
                year=str(song.get("year", "")),
            )
            for song in songs
        ]

    async def update_playlist_image(
        self, playlist_id: str, image_url: str | None
    ) -> None:
        """Set the cover image for a Navidrome playlist.

        The Subsonic API v1.16.1 does **not** expose an endpoint for
        updating playlist images.  A warning is logged if *image_url* is
        provided.
        """

        logger.warning(
            "Navidrome / Subsonic API does not support setting playlist images"
        )

    async def rescan_library(self) -> None:
        """Trigger a full library scan in Navidrome."""

        await self._subsonic("startScan")

    async def is_scanning_library(self) -> bool:
        """Return True if Navidrome is currently scanning its library."""

        data = await self._subsonic("getScanStatus")
        scan_status = data.get("scanStatus", {})

        return bool(scan_status.get("scanning", False))

    async def wait_for_rescan(
        self,
        start_timeout_seconds: int = 30,
        poll_interval_seconds: int = 3,
        scan_poll_interval_seconds: int = 15,
    ) -> None:
        """Trigger a rescan and block until the scan finishes."""

        await self.rescan_library()

        waited = 0
        is_scan_started = False

        while waited < start_timeout_seconds:
            if await self.is_scanning_library():
                is_scan_started = True
                break
            await asyncio.sleep(poll_interval_seconds)
            waited += poll_interval_seconds

        if not is_scan_started:
            logger.warning("Navidrome library scan did not start within expected time")
        else:
            logger.info("Navidrome library scan complete")

    async def update_playlist_visibility(
        self, playlist_name: str, username: str, is_public: bool
    ) -> None:
        """Update the visibility of an existing Navidrome playlist."""

        user = await self.get_user_by_name(username=username)

        if not user:
            logger.warning(
                f"Unable to find Navidrome user '{user}' when updating playlist visibility",
            )
            return

        playlists = await self.get_playlists(user_id=user.id)

        existing = next(
            (
                playlist
                for playlist in playlists
                if playlist.name == playlist_name
                and (playlist.owner_id is None or playlist.owner_id == username)
            ),
            None,
        )

        if not existing:
            logger.warning(
                f"Unable to find existing Navidrome playlist '{playlist_name}' "
                f"for user '{username}' when updating playlist visibility",
            )
            return

        await self._subsonic(
            "updatePlaylist",
            params={
                "playlistId": existing.id,
                "public": "true" if is_public else "false",
            },
            http_method="POST",
        )

        logger.info(
            "Updated Navidrome playlist '%s' visibility to public=%s",
            playlist_name,
            is_public,
        )

    async def ensure_download_library_exists(self) -> None:
        """Check whether the download library exists in Navidrome.

        Navidrome manages its own music directories via its server configuration, so this is a no-op.
        """

        logger.info(
            "Navidrome manages music directories through its own configuration, skipping download library check"
        )
