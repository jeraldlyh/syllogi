from db.models.music_server_user import MusicServerProvider
from db.models.recommendation import RecommendationProvider
from lib.env import (
    get_environment_variable,
    is_jellyfin_configured,
    is_navidrome_configured,
)
from lib.models.provider import ProviderError
from lib.providers.base import MusicPlaylistProvider
from lib.providers.jellyfin import JellyfinProvider
from lib.providers.navidrome import NavidromeProvider
from lib.providers.base import RecommendationSourceProvider


def get_provider() -> MusicPlaylistProvider:
    """Return the configured music provider."""

    override = str(get_environment_variable("MUSIC_PROVIDER")).strip().lower()
    is_jellyfin_enabled = is_jellyfin_configured()
    is_navidrome_enabled = is_navidrome_configured()

    if not is_jellyfin_enabled and not is_navidrome_enabled:
        raise ProviderError(
            "No music provider configured. Set up environment variables for Jellyfin or Navidrome, or set MUSIC_PROVIDER explicitly."
        )

    if override == "jellyfin":
        from lib.providers.jellyfin import JellyfinProvider

        return JellyfinProvider()

    if override == "navidrome":
        from lib.providers.navidrome import NavidromeProvider

        return NavidromeProvider()

    if is_jellyfin_enabled and is_navidrome_enabled:
        raise ProviderError(
            "Both Jellyfin and Navidrome are configured. "
            "Set MUSIC_PROVIDER to 'jellyfin' or 'navidrome' to disambiguate."
        )

    if is_jellyfin_enabled:
        from lib.providers.jellyfin import JellyfinProvider

        return JellyfinProvider()

    if is_navidrome_enabled:
        from lib.providers.navidrome import NavidromeProvider

        return NavidromeProvider()

    raise ProviderError(
        "No music provider configured. Set up environment variables for Jellyfin or Navidrome, or set MUSIC_PROVIDER explicitly."
    )


def get_provider_enum() -> "MusicServerProvider":
    """Return the MusicServerProvider enum value for the configured music provider."""

    provider = get_provider()

    if isinstance(provider, NavidromeProvider):
        return MusicServerProvider.navidrome
    if isinstance(provider, JellyfinProvider):
        return MusicServerProvider.jellyfin

    raise ProviderError("Unable to determine music server provider")


def get_recommendation_provider(
    provider: "RecommendationSourceProvider",
) -> RecommendationSourceProvider:
    """Return the recommendation source provider for the given provider type."""

    if provider == RecommendationProvider.listenbrainz:
        from lib.providers.listenbrainz import ListenBrainzRecommendationProvider

        return ListenBrainzRecommendationProvider()
    elif provider == RecommendationProvider.lastfm:
        from lib.providers.lastfm import LastFMRecommendationProvider

        return LastFMRecommendationProvider()
    else:
        raise ProviderError(f"Unsupported recommendation provider: {provider}")
