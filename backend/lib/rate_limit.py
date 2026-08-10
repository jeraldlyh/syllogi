import asyncio
import time


class TokenBucketRateLimiter:
    """Token bucket rate limiter for async HTTP requests."""

    def __init__(self, rate: int = 50, per: float = 1.0):
        self.rate = rate
        self.per = per
        self._tokens = float(rate)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill

            self._tokens = min(
                self.rate, self._tokens + elapsed * (self.rate / self.per)
            )
            self._last_refill = now

            if self._tokens >= 1:
                self._tokens -= 1
                return

            wait = (1 - self._tokens) * (self.per / self.rate)

        await asyncio.sleep(wait)

        async with self._lock:
            self._tokens -= 1
