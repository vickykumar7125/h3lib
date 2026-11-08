"""Cache backends for h3lib."""

from h3lib.cache.base import Cache
from h3lib.cache.factory import create_cache
from h3lib.cache.memory import InMemoryCache

__all__ = [
    "Cache",
    "InMemoryCache",
    "RedisCache",
    "create_cache",
]


def __getattr__(name: str):
    if name == "RedisCache":
        from h3lib.cache.redis_cache import RedisCache

        return RedisCache
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
