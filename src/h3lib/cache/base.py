"""Cache backend protocol / ABC."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any


class Cache(ABC):
    """Cache H3 cell payloads."""

    @abstractmethod
    def get(self, cell: str) -> dict[str, Any] | None:
        """Return cached payload, or None on miss."""

    @abstractmethod
    def set(self, cell: str, payload: Mapping[str, Any] | None, ttl: int | None = None) -> None:
        """Store payload under cell key."""

    @abstractmethod
    def delete(self, cell: str) -> None:
        """Invalidate a cell key."""

    @abstractmethod
    def get_many(self, cells: Iterable[str]) -> dict[str, dict[str, Any]]:
        """Return found cached entries."""

    @abstractmethod
    def set_many(
        self,
        items: Mapping[str, Mapping[str, Any] | None],
        ttl: int | None = None,
    ) -> None:
        """Bulk set."""

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries managed by this backend."""

    @abstractmethod
    def close(self) -> None:
        """Release resources."""

    def __enter__(self) -> Cache:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
