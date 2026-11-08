"""Cache factory helpers."""

from __future__ import annotations

from typing import Any

from h3lib.cache.base import Cache
from h3lib.cache.memory import InMemoryCache
from h3lib.exceptions import ConfigurationError


def create_cache(
    enabled: bool = False,
    *,
    redis_url: str | None = None,
    redis_client: Any | None = None,
    backend: str | None = None,
    **kwargs: Any,
) -> Cache | None:
    """
    Create a cache backend according to policy:

    - enabled=False -> None (no cache), regardless of backend=
    - enabled=True + explicit backend=memory -> InMemory (even if redis_url set)
    - enabled=True + redis_url/redis_client/backend=redis -> Redis
    - enabled=True otherwise -> InMemory
    """
    if not enabled:
        return None

    chosen = (backend or "").strip().lower() if backend else None

    if chosen in {"none", "off", "disabled"}:
        return None

    if chosen in {"memory", "mem", "inmemory"}:
        return InMemoryCache()

    use_redis = (
        chosen in {"redis"}
        or redis_url is not None
        or redis_client is not None
    )

    if use_redis:
        from h3lib.cache.redis_cache import RedisCache

        if redis_client is not None:
            return RedisCache(client=redis_client, **kwargs)
        return RedisCache(url=redis_url or "redis://localhost:6379/0", **kwargs)

    if chosen in {None, ""}:
        return InMemoryCache()

    raise ConfigurationError(
        f"Unknown cache backend '{backend}'. Choose: memory, redis, none"
    )
