from abc import ABC, abstractmethod

from lib.models.common import RecommendationTrack


class RecommendationSourceProvider(ABC):
    """Abstract base class for recommendation source providers."""

    @abstractmethod
    async def get_top_tracks(
        self,
        *,
        username: str,
        period: str = "6month",
        limit: int = 30,
    ) -> list[RecommendationTrack]:
        """Return top tracks for a given user and time period."""
        ...

    @abstractmethod
    async def get_recent_tracks(
        self,
        *,
        username: str,
        limit: int = 30,
    ) -> list[RecommendationTrack]:
        """Return recently played tracks for a given user."""
        ...

    @abstractmethod
    async def get_similar_tracks(
        self,
        *,
        artist_name: str,
        track_name: str,
        musicbrainz_id: str = "",
        count: int = 10,
    ) -> list[RecommendationTrack]:
        """Return tracks similar to the given seed track."""
        ...

    @abstractmethod
    async def verify_username(self, username: str) -> bool:
        """Check whether the given username exists in the recommendation source."""
        ...
