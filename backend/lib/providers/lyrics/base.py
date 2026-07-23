from abc import ABC, abstractmethod


class LyricsProvider(ABC):
    """Abstract base class for lyrics metadata providers."""

    @abstractmethod
    async def get_lyrics(
        self,
        *,
        artist_name: str,
        track_name: str,
        album_name: str,
        duration: int,
    ) -> str | None:
        """Get track lyrics.

        Args:
            artist_name: Name of the artist.
            track_name: Name of the track.
            album_name: Name of the album.
            duration: Track's duration in seconds.

        Returns:
            str containing the lyrics, or None if not found.
        """
        ...
