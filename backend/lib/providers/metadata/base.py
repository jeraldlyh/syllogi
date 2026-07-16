from abc import ABC, abstractmethod

from lib.models.metadata import AlbumInfo, ArtistInfo, ArtistTrack


class MetadataProvider(ABC):
    """Abstract base class for artist metadata providers."""

    @abstractmethod
    async def get_artist_info(
        self,
        *,
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
    async def get_artist_tracks(
        self, *, artist_mbid: str, limit: int
    ) -> list[ArtistTrack]:
        """Get artist tracks by MusicBrainz ID.

        Args:
            artist_mbid: MusicBrainz ID to search for.
            limit: Maximum number of tracks to return.

        Returns:
            List of ArtistTrack.
        """
        ...

    @abstractmethod
    async def get_artist_track(
        self, *, artist_name: str, track_name: str
    ) -> list[ArtistTrack]:
        """Get artist track by name

        Args:
            artist_name: Artist name to search for.
            track_name: Track name to search for.

        Returns:
            List of ArtistTrack.
        """

    @abstractmethod
    async def get_album_info(
        self,
        *,
        artist_name: str,
        album_name: str,
    ) -> AlbumInfo | None:
        """Get album metadata and tracklist by artist and album name.

        Args:
            artist_name: Artist name.
            album_name: Album name.

        Returns:
            An AlbumInfo instance with tracks, or None if not found.
        """
        ...
