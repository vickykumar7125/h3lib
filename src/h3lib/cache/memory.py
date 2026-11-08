"""In-memory cache backend."""

from __future__ import annotations

import threading
import time
from collections.abc import Iterable, Mapping
from typing import Any

from h3lib.cache.base import Cache


class InMemoryCache(Cache):
    def __init__(self) -> None:
        # cell -> (payload, expires_at|None)
        self._data: dict[str, tuple[dict[str, Any], float | None]] = {}
        self._lock = threading.RLock()

    def _alive(self, cell: str) -> dict[str, Any] | None:
        item = self._data.get(cell)
        if item is None:
            return None
        payload, expires_at = item
        if expires_at is not None and time.time() >= expires_at:
            del self._data[cell]
            return None
        return payload

    def get(self, cell: str) -> dict[str, Any] | None:
        with self._lock:
            return self._alive(cell)

    def set(self, cell: str, payload: Mapping[str, Any] | None, ttl: int | None = None) -> None:
        expires_at = (time.time() + ttl) if ttl is not None else None
        with self._lock:
            self._data[cell] = (dict(payload or {}), expires_at)

    def delete(self, cell: str) -> None:
        with self._lock:
            self._data.pop(cell, None)

    def get_many(self, cells: Iterable[str]) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        with self._lock:
            for cell in cells:
                payload = self._alive(cell)
                if payload is not None:
                    out[cell] = payload
        return out

    def set_many(
        self,
        items: Mapping[str, Mapping[str, Any] | None],
        ttl: int | None = None,
    ) -> None:
        expires_at = (time.time() + ttl) if ttl is not None else None
        with self._lock:
            for cell, payload in items.items():
                self._data[cell] = (dict(payload or {}), expires_at)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def close(self) -> None:
        self.clear()
