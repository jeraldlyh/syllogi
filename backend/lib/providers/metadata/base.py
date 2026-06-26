from abc import ABC, abstractmethod

from lib.models.metadata import ArtistInfo


class MetadataSourceProvider(ABC):
    """Abstract base class for artist metadata providers."""

    @abstractmethod
    async def get_artist_info(
        self,
        artist_name: str,
    ) -> ArtistInfo | None:
        """Get artist metadata by name.

        Args:
            artist_name: Artist name to search for.

        Returns:
            An ArtistMetadata instance, or None if not found.
        """
        ...
