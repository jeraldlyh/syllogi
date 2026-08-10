import asyncio
import time
from unittest.mock import AsyncMock

from lib.rate_limit import TokenBucketRateLimiter


class _FakeClock:
    """Callable stand-in for time.monotonic with controllable values."""

    def __init__(self, start: float = 100.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TestTokenBucketRateLimiter:
    async def test_acquire_immediately_when_tokens_available(self, monkeypatch):
        clock = _FakeClock()
        monkeypatch.setattr(time, "monotonic", clock)

        sleep = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", sleep)

        limiter = TokenBucketRateLimiter(rate=50, per=1.0)

        result = await limiter.acquire()

        assert result is None
        sleep.assert_not_called()

    async def test_acquire_depletes_token(self, monkeypatch):
        clock = _FakeClock()
        monkeypatch.setattr(time, "monotonic", clock)
        monkeypatch.setattr(asyncio, "sleep", AsyncMock())

        limiter = TokenBucketRateLimiter(rate=50, per=1.0)
        assert limiter._tokens == 50.0

        await limiter.acquire()
        assert limiter._tokens == 49.0

        await limiter.acquire()
        assert limiter._tokens == 48.0

    async def test_acquire_waits_when_no_tokens(self, monkeypatch):
        clock = _FakeClock()
        monkeypatch.setattr(time, "monotonic", clock)

        sleep = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", sleep)

        limiter = TokenBucketRateLimiter(rate=1, per=1.0)

        await limiter.acquire()
        sleep.assert_not_called()

        await limiter.acquire()
        sleep.assert_called_once_with(1.0)

        assert limiter._tokens == -1.0

    async def test_tokens_refill_over_time(self, monkeypatch):
        clock = _FakeClock()
        monkeypatch.setattr(time, "monotonic", clock)

        sleep = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", sleep)

        limiter = TokenBucketRateLimiter(rate=10, per=1.0)
        for _ in range(10):
            await limiter.acquire()
        assert limiter._tokens == 0.0

        clock.advance(0.5)
        await limiter.acquire()

        assert limiter._tokens == 4.0
        sleep.assert_not_called()

    async def test_tokens_capped_at_rate(self, monkeypatch):
        clock = _FakeClock()
        monkeypatch.setattr(time, "monotonic", clock)
        sleep = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", sleep)

        limiter = TokenBucketRateLimiter(rate=10, per=1.0)
        for _ in range(10):
            await limiter.acquire()
        assert limiter._tokens == 0.0

        clock.advance(10_000)
        await limiter.acquire()

        assert limiter._tokens == 9.0
        sleep.assert_not_called()

    async def test_concurrent_acquires(self):
        limiter = TokenBucketRateLimiter(rate=10, per=1.0)
        n = 12

        start = time.monotonic()
        results = await asyncio.gather(*(limiter.acquire() for _ in range(n)))
        elapsed = time.monotonic() - start

        assert len(results) == n
        assert all(result is None for result in results)
        assert elapsed >= 0.09
        assert elapsed < 5.0

    async def test_custom_rate_and_per(self, monkeypatch):
        clock = _FakeClock()
        monkeypatch.setattr(time, "monotonic", clock)

        sleep = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", sleep)

        limiter = TokenBucketRateLimiter(rate=2, per=2.0)
        await limiter.acquire()
        await limiter.acquire()
        sleep.assert_not_called()

        await limiter.acquire()

        sleep.assert_called_once_with(1.0)
        sleep.reset_mock()

        limiter = TokenBucketRateLimiter(rate=10, per=0.5)
        for _ in range(10):
            await limiter.acquire()
        await limiter.acquire()

        sleep.assert_called_once_with(0.05)
