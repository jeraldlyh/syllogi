from abc import ABC, abstractmethod

from lib.models.metadata import ArtistInfo, ArtistTrack


class MetadataSourceProvider(ABC):
    """Abstract base class for artist metadata providers."""

    @abstractmethod
    async def get_artist_info(
        self,
        artist_name: str,
        locale: str | None = None,
    ) -> ArtistInfo | None:
        """Get artist metadata by name.

        Args:
            artist_name: Artist name to search for.

        Returns:
            An ArtistMetadata instance, or None if not found.
        """
        ...

    @abstractmethod
    async def get_artist_recordings(
        self, artist_mbid: str, limit: int
    ) -> list[ArtistTrack]:
        """Get artist recordings by MusicBrainz ID.

        Args:
            artist_mbid: MusicBrainz ID to search for.
            limit: Maximum number of recordings to return.

        Returns:
            List of ArtistTrack.
        """
        ...
