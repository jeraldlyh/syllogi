from abc import ABC, abstractmethod

from lib.models.provider import ProviderTrack, ProviderPlaylist, ProviderUser


class MusicPlaylistProvider(ABC):
    """Abstract base class for music server providers."""

    @abstractmethod
    async def get_users(self) -> list[ProviderUser]:
        """Return all users registered in the music server."""
        ...

    @abstractmethod
    async def get_user_by_name(self, username: str) -> ProviderUser | None:
        """Find a user by their username."""
        ...

    @abstractmethod
    async def get_playlists(self, user_id: str) -> list[ProviderPlaylist]:
        """Return all playlists visible to the given user."""
        ...

    @abstractmethod
    async def get_or_create_playlist(
        self, playlist_name: str, username: str, is_public: bool = False
    ) -> tuple[str, str]:
        """Get an existing playlist by name or create a new one.

        Returns:
            tuple[str, str]: (playlist_id, user_id)
        """
        ...

    @abstractmethod
    async def create_playlist(
        self, playlist_name: str, user_id: str, is_public: bool = False
    ) -> ProviderPlaylist:
        """Create a new playlist owned by the given user."""
        ...

    @abstractmethod
    async def delete_playlist(self, playlist_id: str) -> None:
        """Delete a playlist by its ID."""
        ...

    @abstractmethod
    async def get_playlist_songs(
        self, playlist_id: str, user_id: str
    ) -> list[ProviderTrack]:
        """Return all tracks in a playlist."""
        ...

    @abstractmethod
    async def add_songs_to_playlist(
        self, playlist_id: str, user_id: str, track_ids: list[str]
    ) -> None:
        """Append tracks to an existing playlist."""
        ...

    @abstractmethod
    async def delete_songs_from_playlist(
        self, playlist_id: str, entry_ids: list[str]
    ) -> None:
        """Remove tracks from a playlist by their entry IDs."""
        ...

    @abstractmethod
    async def search_track(
        self, artist_name: str, title: str, album: str, year: str
    ) -> list[ProviderTrack]:
        """Search for audio tracks matching the given metadata."""
        ...

    @abstractmethod
    async def update_playlist_image(
        self, playlist_id: str, image_url: str | None
    ) -> None:
        """Set the primary cover image for a playlist from a remote URL."""
        ...

    @abstractmethod
    async def rescan_library(self) -> None:
        """Trigger a full metadata refresh on the configured download library."""
        ...

    @abstractmethod
    async def is_scanning_library(self) -> bool:
        """Return True if the configured download library is currently being scanned."""
        ...

    @abstractmethod
    async def wait_for_rescan(
        self,
        poll_interval_seconds: int = 15,
        max_wait_seconds: int = 600,
    ) -> None:
        """Trigger a rescan and block until the server finishes indexing."""
        ...

    @abstractmethod
    async def update_playlist_visibility(
        self, playlist_name: str, username: str, is_public: bool
    ) -> None:
        """Update the visibility of an existing playlist. Override in providers that support it."""
        ...

    async def verify_user_credentials(self, username: str, password: str) -> bool:
        """Verify that the given username/password pair is valid against the music server.

        Override in providers that support credential verification.
        """
        return True

    @abstractmethod
    async def ensure_download_library_exists(self) -> None:
        """Check whether the download library exists and create it if not."""
        ...
