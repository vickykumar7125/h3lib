"""Redis cache backend (optional)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from h3lib._util import dumps_payload, loads_payload, require_module
from h3lib.cache.base import Cache
from h3lib.exceptions import ConfigurationError


class RedisCache(Cache):
    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        *,
        prefix: str = "h3lib:",
        client: Any | None = None,
        default_ttl: int | None = None,
    ) -> None:
        redis = require_module("redis", "redis")
        if not prefix:
            raise ConfigurationError(
                "Redis cache prefix must be non-empty; "
                "an empty prefix would match all keys on clear()"
            )
        self._prefix = prefix
        self._default_ttl = default_ttl
        self._owns_client = client is None
        self._client = client or redis.Redis.from_url(url, decode_responses=True)

    def _key(self, cell: str) -> str:
        return f"{self._prefix}{cell}"

    def get(self, cell: str) -> dict[str, Any] | None:
        raw = self._client.get(self._key(cell))
        return loads_payload(raw)

    def set(self, cell: str, payload: Mapping[str, Any] | None, ttl: int | None = None) -> None:
        key = self._key(cell)
        value = dumps_payload(payload)
        effective = ttl if ttl is not None else self._default_ttl
        if effective is not None:
            self._client.set(key, value, ex=int(effective))
        else:
            self._client.set(key, value)

    def delete(self, cell: str) -> None:
        self._client.delete(self._key(cell))

    def get_many(self, cells: Iterable[str]) -> dict[str, dict[str, Any]]:
        cell_list = list(cells)
        if not cell_list:
            return {}
        keys = [self._key(c) for c in cell_list]
        values = self._client.mget(keys)
        out: dict[str, dict[str, Any]] = {}
        for cell, raw in zip(cell_list, values, strict=False):
            loaded = loads_payload(raw)
            if loaded is not None:
                out[cell] = loaded
        return out

    def set_many(
        self,
        items: Mapping[str, Mapping[str, Any] | None],
        ttl: int | None = None,
    ) -> None:
        pipe = self._client.pipeline()
        effective = ttl if ttl is not None else self._default_ttl
        for cell, payload in items.items():
            key = self._key(cell)
            value = dumps_payload(payload)
            if effective is not None:
                pipe.set(key, value, ex=int(effective))
            else:
                pipe.set(key, value)
        pipe.execute()

    def clear(self) -> None:
        """
        Delete keys under this cache prefix only.

        Uses SCAN+DELETE; concurrent writers may recreate keys during the scan.
        Prefix must be non-empty (enforced in __init__) so this never matches '*'.
        """
        pattern = f"{self._prefix}*"
        cursor = 0
        while True:
            cursor, keys = self._client.scan(cursor=cursor, match=pattern, count=500)
            if keys:
                self._client.delete(*keys)
            if cursor == 0:
                break

    def close(self) -> None:
        if not self._owns_client:
            return
        try:
            self._client.close()
        except Exception:
            pass
