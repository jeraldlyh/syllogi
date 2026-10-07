import asyncio
from typing import cast
from unittest.mock import AsyncMock

import httpx
import pytest

from app import wait_for_provider_ready
from lib.providers.playlist.base import MusicPlaylistProvider

_JELLYFIN_URL = "http://jellyfin.example.com"


def _http_status_error() -> httpx.HTTPStatusError:
    return httpx.HTTPStatusError(
        "503 Service Unavailable",
        request=httpx.Request("GET", f"{_JELLYFIN_URL}/Library/VirtualFolders"),
        response=httpx.Response(503),
    )


class _FakeProvider:
    """Minimal stand-in exposing the one method wait_for_provider_ready calls."""

    def __init__(self, errors: list[Exception]) -> None:
        self._errors = list(errors)
        self.calls = 0

    async def ensure_download_library_exists(self) -> None:
        self.calls += 1

        if self._errors:
            raise self._errors.pop(0)


class TestWaitForProviderReady:
    async def test_retries_connect_errors_until_success(self, monkeypatch):
        sleep = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", sleep)

        provider = _FakeProvider(
            [httpx.ConnectError("connection refused"), httpx.ConnectError("refused")]
        )

        await wait_for_provider_ready(cast(MusicPlaylistProvider, provider))

        assert provider.calls == 3
        assert sleep.call_count == 2

    async def test_raises_runtime_error_after_max_attempts(self, monkeypatch):
        sleep = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", sleep)

        provider = _FakeProvider([_http_status_error()] * 3)

        with pytest.raises(RuntimeError, match="did not become ready after 3 attempts"):
            await wait_for_provider_ready(
                cast(MusicPlaylistProvider, provider),
                max_attempts=3,
                initial_delay=0.01,
            )

        assert provider.calls == 3
        assert sleep.call_count == 2

    async def test_non_retryable_error_propagates_immediately(self, monkeypatch):
        sleep = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", sleep)

        provider = _FakeProvider([ValueError("bad config")])

        with pytest.raises(ValueError, match="bad config"):
            await wait_for_provider_ready(cast(MusicPlaylistProvider, provider))

        assert provider.calls == 1
        assert sleep.call_count == 0
