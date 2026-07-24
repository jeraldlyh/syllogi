import functools
import hashlib
import json
import logging
from typing import Any, Callable, TypeVar

from cachetools import TTLCache

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def _make_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Build a stable cache key from function name and arguments."""

    key_parts = [func_name]

    key_parts.extend(repr(a) for a in args)
    key_parts.extend(f"{k}={repr(v)}" for k, v in sorted(kwargs.items()))

    raw = json.dumps(key_parts, default=str, sort_keys=True)

    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def cached_method(ttl: int = 3600, maxsize: int = 1024):
    """Cache decorator for async instance methods.

    Args:
        ttl: Time-to-live in seconds. Default 1 hour.
        maxsize: Maximum cache entries. Default 1024.
    """

    def decorator(method: F) -> F:
        cache = TTLCache(maxsize=maxsize, ttl=ttl)

        @functools.wraps(method)
        async def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            key = _make_cache_key(method.__name__, args, kwargs)

            if key in cache:
                logger.debug(f"Cache hit: {method.__name__}")
                return cache[key]

            result = await method(self, *args, **kwargs)

            if result is not None and result != []:
                cache[key] = result
            return result

        wrapper.cache = cache  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorator


def cached_function(ttl: int = 1800, maxsize: int = 256):
    """Cache decorator for sync functions (not methods).

    Args:
        ttl: Time-to-live in seconds. Default 30 minutes.
        maxsize: Maximum cache entries. Default 256.
    """

    def decorator(func: F) -> F:
        cache = TTLCache(maxsize=maxsize, ttl=ttl)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = _make_cache_key(func.__name__, args, kwargs)
            if key in cache:
                logger.debug(f"Cache hit: {func.__name__}")
                return cache[key]
            result = func(*args, **kwargs)

            if result is not None and result != []:
                cache[key] = result
            return result

        wrapper.cache = cache  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorator
