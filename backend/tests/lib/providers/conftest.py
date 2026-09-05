import inspect
import json
from pathlib import Path

import pytest

from lib.providers.metadata.deezer import DeezerMetadataProvider
from lib.providers.metadata.lastfm import LastFMMetadataProvider
from lib.providers.metadata.musicbrainz import (
    MusicBrainzMetadataProvider,
    _musicbrainz_limiter,
)
from lib.providers.recommendation.lastfm import LastFMRecommendationProvider
from lib.providers.recommendation.listenbrainz import ListenBrainzRecommendationProvider

_PROVIDER_CLASSES = (
    DeezerMetadataProvider,
    LastFMMetadataProvider,
    MusicBrainzMetadataProvider,
    LastFMRecommendationProvider,
    ListenBrainzRecommendationProvider,
)


def load_fixture(name: str) -> dict:
    """Load a JSON fixture file from the fixtures directory of the calling test file."""
    caller_frame = inspect.stack()[1]
    caller_file = Path(caller_frame.filename).parent / "fixtures" / f"{name}.json"

    with open(caller_file) as f:
        return json.load(f)


@pytest.fixture(autouse=True)
def _provider_env(monkeypatch):
    """Provide provider API keys and URLs so HTTP helpers do not raise any errors.

    get_environment_variable(..., ignore_error=False) is used by Last.fm and
    ListenBrainz HTTP helpers, so the API keys must be set even though all
    HTTP calls are mocked with respx.
    """
    monkeypatch.setenv("LASTFM_API_KEY", "test-lastfm-api-key")
    monkeypatch.setenv("LASTFM_URL", "https://ws.audioscrobbler.com/2.0/")
    monkeypatch.setenv("LISTENBRAINZ_API_KEY", "test-listenbrainz-api-key")
    monkeypatch.setenv("LISTENBRAINZ_URL", "https://api.listenbrainz.org")
    monkeypatch.setenv("MUSICBRAINZ_URL", "https://musicbrainz.org/ws/2")
    monkeypatch.setenv("MUSICBRAINZ_USER_AGENT", "syllogi/0.1.0 (test)")


@pytest.fixture(autouse=True)
def _set_musicbrainz_limiter(monkeypatch):
    """Lift the MusicBrainz rate limit for tests."""
    monkeypatch.setattr(_musicbrainz_limiter, "rate", 1000)
    monkeypatch.setattr(_musicbrainz_limiter, "_tokens", 1000.0)


@pytest.fixture(autouse=True)
def _clear_provider_caches():
    """Clear @cached_method caches before each test.

    cached_method keeps a single cache per method that is shared across all
    provider instances, so creating fresh instances is not enough to avoid
    cache hits between tests that use the same arguments.
    """
    for provider_class in _PROVIDER_CLASSES:
        for attr in vars(provider_class).values():
            cache = getattr(attr, "cache", None)
            if cache is not None:
                cache.clear()
    yield
