from abc import ABC, abstractmethod

from lib.models.library import LyricsCandidate

MAX_SEARCH_RESULTS = 20


class LyricsProvider(ABC):
    """Abstract base class for lyrics metadata providers."""

    @abstractmethod
    async def search_lyrics(
        self,
        *,
        query: str = "",
        artist_name: str = "",
        track_name: str = "",
        album_name: str = "",
        limit: int = 20,
    ) -> list[LyricsCandidate]:
        """Search for lyrics matching a track.

        Args:
            query: Free-text search, used instead of the fields below.
            artist_name: Name of the artist.
            track_name: Name of the track.
            album_name: Name of the album.
            limit: Maximum number of candidates to return.

        Returns:
            The matching candidates, best match first. Empty if none were found.
        """
        ...
