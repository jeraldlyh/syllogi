import asyncio
import hashlib
import logging
import secrets
from typing import Any

import httpx

from lib.env import get_environment_variable
from lib.models.provider import (
    ProviderError,
    ProviderPlaylist,
    ProviderTrack,
    ProviderUser,
)
from lib.providers.playlist.base import MusicPlaylistProvider

logger = logging.getLogger(__name__)


class NavidromeProvider(MusicPlaylistProvider):
    """Navidrome music server provider using the Subsonic REST API v1.16.1."""

    def __init__(self) -> None:
        self._bearer_token: str | None = None

    async def _subsonic(
        self,
        method: str,
        *,
        username: str,
        password: str,
        params: dict[str, Any] | None = None,
        http_method: str = "GET",
        timeout: float = 30.0,
    ) -> Any:
        """HTTP helper for the Subsonic API (authenticated with explicit user credentials)."""

        url = str(get_environment_variable("NAVIDROME_URL", ignore_error=False))

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

    async def _subsonic_admin(
        self,
        method: str,
        *,
        params: dict[str, Any] | None = None,
        http_method: str = "GET",
        timeout: float = 30.0,
    ) -> Any:
        """Subsonic API call using admin credentials from environment variables."""

        username = str(
            get_environment_variable("NAVIDROME_USERNAME", ignore_error=False)
        )
        password = str(
            get_environment_variable("NAVIDROME_PASSWORD", ignore_error=False)
        )
        return await self._subsonic(
            method,
            username=username,
            password=password,
            params=params,
            http_method=http_method,
            timeout=timeout,
        )

    async def _get_bearer_token(self) -> str | None:
        """Obtain a JWT bearer token from Navidrome's auth/login endpoint.

        The token is cached on the instance for reuse across calls.
        """

        if self._bearer_token:
            return self._bearer_token

        url = str(get_environment_variable("NAVIDROME_URL"))
        username = str(get_environment_variable("NAVIDROME_USERNAME"))
        password = str(get_environment_variable("NAVIDROME_PASSWORD"))

        if not url or not username or not password:
            logger.error(
                "NAVIDROME_URL, NAVIDROME_USERNAME, and NAVIDROME_PASSWORD must be set for http API access"
            )
            return None

        login_url = f"{url.rstrip('/')}/auth/login"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    login_url,
                    json={"username": username, "password": password},
                    timeout=30.0,
                )
            response.raise_for_status()
            body = response.json()
            token: str | None = body.get("token")

            if not token:
                logger.error("Navidrome auth/login response missing 'token' field")
                return None
            self._bearer_token = token

            return token
        except Exception as exc:
            logger.error(f"Failed to obtain Navidrome bearer token: {exc}")
            return None

    async def _api(
        self,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        http_method: str = "GET",
        timeout: float = 30.0,
    ) -> Any:
        """HTTP helper for the Navidrome HTTP REST API (bearer token auth).

        Automatically obtains and caches a the bearer token.

        Returns the parsed JSON body on success, or an empty dict on failure.
        """

        token = await self._get_bearer_token()

        if not token:
            return {}

        url = str(get_environment_variable("NAVIDROME_URL"))

        if not url:
            logger.error("NAVIDROME_URL is not configured")
            return {}

        request_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}"

        headers = {
            "X-ND-Authorization": f"Bearer {token}",
        }

        async def _http() -> Any:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=http_method.upper(),
                    url=request_url,
                    params=params,
                    headers=headers,
                    timeout=timeout,
                )
            response.raise_for_status()
            return response.json()

        try:
            return await _http()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                logger.info(
                    "Navidrome bearer token expired, refreshing token and retrying request"
                )

                self._bearer_token = None
                token = await self._get_bearer_token()

                if not token:
                    return {}

                headers["X-ND-Authorization"] = f"Bearer {token}"

                try:
                    return await _http()
                except Exception as retry_exc:
                    logger.error(
                        f"Navidrome http error after retrying with new token {retry_exc}"
                    )
                    return {}
            logger.error(
                f"Navidrome HTTP API HTTP error {exc.response.status_code}: {exc}",
            )
            return {}
        except Exception as exc:
            logger.error("Navidrome http error request error: %s", exc)
            return {}

    async def get_users(self) -> list[ProviderUser]:
        """Return all users registered in Navidrome via the HTTP API."""

        all_users: list[dict[str, Any]] = []
        start = 0
        page_size = 100

        while True:
            page = await self._api(
                "api/user",
                params={
                    "_start": str(start),
                    "_end": str(start + page_size),
                    "_sort": "userName",
                    "_order": "ASC",
                },
            )
            if not isinstance(page, list) or not page:
                break
            all_users.extend(page)
            if len(page) < page_size:
                break
            start += page_size

        return [
            ProviderUser(id=str(user.get("id", "")), name=user.get("userName", ""))
            for user in all_users
            if user.get("id") and user.get("userName")
        ]

    async def get_user_by_name(self, username: str) -> ProviderUser | None:
        """Find a Navidrome user by their username via the HTTP API."""

        users = await self.get_users()
        for user in users:
            if user.name == username:
                return user
        return None

    async def get_playlists(
        self,
        *,
        user_id: str,
        username: str = "",
        password: str = "",
    ) -> list[ProviderPlaylist]:
        """Return all playlists visible to the given Navidrome user."""

        data = await self._subsonic(
            "getPlaylists", username=username, password=password
        )
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
        self,
        *,
        playlist_name: str,
        username: str,
        is_public: bool = False,
        password: str = "",
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

        playlists = await self.get_playlists(
            user_id=user.id, username=username, password=password
        )

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
                username=username,
                password=password,
            )
            playlist_id = new_playlist.id

            if not playlist_id:
                raise ProviderError("Unable to create new playlist in Navidrome")

        await self.update_playlist_visibility(
            playlist_name=playlist_name,
            username=username,
            is_public=is_public,
            password=password,
        )

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
        """Create a new playlist in Navidrome."""

        data = await self._subsonic(
            "createPlaylist",
            params={"name": playlist_name},
            http_method="POST",
            username=username,
            password=password,
        )

        playlist = data.get("playlist", {})

        return ProviderPlaylist(
            id=playlist.get("id", ""),
            name=playlist.get("name", playlist_name),
            owner_id=playlist.get("owner"),
        )

    async def delete_playlist(
        self,
        *,
        playlist_id: str,
        username: str = "",
        password: str = "",
    ) -> None:
        """Delete a Navidrome playlist by its ID."""

        await self._subsonic(
            "deletePlaylist",
            params={"id": playlist_id},
            http_method="POST",
            username=username,
            password=password,
        )

    async def get_playlist_songs(
        self,
        *,
        playlist_id: str,
        user_id: str,
        username: str = "",
        password: str = "",
    ) -> list[ProviderTrack]:
        """Return all tracks in a Navidrome playlist."""

        data = await self._subsonic(
            "getPlaylist",
            params={"id": playlist_id},
            username=username,
            password=password,
        )
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
                musicbrainz_id=entry.get("musicBrainzId", ""),
                artists=([entry["artist"]] if entry.get("artist") else []),
                duration_ticks=int(entry.get("duration", 0)) * 10_000_000,
                year=str(entry.get("year", "")),
            )
            for entry in entries
        ]

    async def add_songs_to_playlist(
        self,
        *,
        playlist_id: str,
        user_id: str,
        track_ids: list[str],
        username: str = "",
        password: str = "",
    ) -> None:
        """Append tracks to an existing Navidrome playlist."""

        await self._subsonic(
            "updatePlaylist",
            params={
                "playlistId": playlist_id,
                "songIdToAdd": track_ids,
            },
            http_method="POST",
            username=username,
            password=password,
        )

    async def delete_songs_from_playlist(
        self,
        *,
        playlist_id: str,
        entry_ids: list[str],
        username: str = "",
        password: str = "",
    ) -> None:
        """Remove tracks from a Navidrome playlist by their track IDs.

        Converts track IDs to 0-based playlist indices for the Subsonic API.
        """

        data = await self._subsonic(
            "getPlaylist",
            params={"id": playlist_id},
            username=username,
            password=password,
        )
        playlist = data.get("playlist", {})
        entries = playlist.get("entry", [])

        if isinstance(entries, dict):
            entries = [entries]

        id_to_index = {entry.get("id"): idx for idx, entry in enumerate(entries)}

        indices_to_remove = [id_to_index[id] for id in entry_ids if id in id_to_index]

        indices_to_remove.sort(reverse=True)

        if not indices_to_remove:
            return

        await self._subsonic(
            "updatePlaylist",
            params={
                "playlistId": playlist_id,
                "songIndexToRemove": [str(idx) for idx in indices_to_remove],
            },
            http_method="POST",
            username=username,
            password=password,
        )

    async def search_track(
        self, *, artist_name: str, title: str, album: str, year: str
    ) -> list[ProviderTrack]:
        """Search for tracks in Navidrome matching the given metadata."""

        logger.info(
            f"Searching for track with artist='{artist_name}', title='{title}', album='{album}', year='{year}'",
        )

        query = f"{artist_name} {title}".strip()
        data = await self._subsonic_admin(
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
                musicbrainz_id=song.get("musicBrainzId", ""),
                artists=([song["artist"]] if song.get("artist") else []),
                duration_ticks=int(song.get("duration", 0)) * 10_000_000,
                year=str(song.get("year", "")),
            )
            for song in songs
        ]

    async def update_playlist_image(
        self, *, playlist_id: str, image_url: str | None
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

        await self._subsonic_admin("startScan")

    async def is_scanning_library(self) -> bool:
        """Return True if Navidrome is currently scanning its library."""

        data = await self._subsonic_admin("getScanStatus")
        scan_status = data.get("scanStatus", {})

        return bool(scan_status.get("scanning", False))

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
                logger.info("Navidrome library scan complete")
                return
            await asyncio.sleep(poll_interval_seconds)
            waited += poll_interval_seconds

        logger.warning(
            f"Navidrome library scan did not complete within {max_wait_seconds}s"
        )

    async def update_playlist_visibility(
        self,
        *,
        playlist_name: str,
        username: str,
        is_public: bool,
        password: str = "",
    ) -> None:
        """Update the visibility of an existing Navidrome playlist."""

        user = await self.get_user_by_name(username=username)

        if not user:
            logger.warning(
                f"Unable to find Navidrome user '{user}' when updating playlist visibility",
            )
            return

        playlists = await self.get_playlists(
            user_id=user.id, username=username, password=password
        )

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
            username=username,
            password=password,
        )

        logger.info(
            "Updated Navidrome playlist '%s' visibility to public=%s",
            playlist_name,
            is_public,
        )

    async def verify_user_credentials(self, username: str, password: str) -> bool:
        """Verify that the given username/password pair is valid against Navidrome."""

        url = str(get_environment_variable("NAVIDROME_URL", ignore_error=False))
        if not url:
            return False

        salt = secrets.token_urlsafe(8)
        token = hashlib.md5((password + salt).encode("utf-8")).hexdigest()

        params = {
            "u": username,
            "t": token,
            "s": salt,
            "v": "1.16.1",
            "c": "syllogi",
            "f": "json",
        }

        request_url = f"{url.rstrip('/')}/rest/ping"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(request_url, params=params, timeout=10.0)

            response.raise_for_status()
            body = response.json()
            subsonic_response = body.get("subsonic-response", {})

            return subsonic_response.get("status") == "ok"
        except Exception as exc:
            logger.warning(
                f"Navidrome credential verification failed for user '{username}': {exc}"
            )
            return False

    async def ensure_download_library_exists(self) -> None:
        """Check whether the download library exists in Navidrome.

        Navidrome manages its own music directories via its server configuration, so this is a no-op.
        """

        logger.info(
            "Navidrome manages music directories through its own configuration, skipping download library check"
        )
