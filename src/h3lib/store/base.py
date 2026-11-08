"""Store backend protocol / ABC."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any


class Store(ABC):
    """Persist H3 cell -> JSON-serializable payload mappings."""

    @property
    def supports_native_h3(self) -> bool:
        """True when the backend can expand H3 neighborhoods inside the DB."""
        return False

    @abstractmethod
    def put(self, cell: str, payload: Mapping[str, Any] | None = None) -> None:
        """Insert or replace a cell record."""

    @abstractmethod
    def get(self, cell: str) -> dict[str, Any] | None:
        """Return payload for a cell, or None if missing."""

    @abstractmethod
    def delete(self, cell: str) -> bool:
        """Delete a cell. Return True if a row was removed."""

    @abstractmethod
    def get_many(self, cells: Iterable[str]) -> dict[str, dict[str, Any]]:
        """Return a mapping of found cells to payloads."""

    @abstractmethod
    def put_many(self, items: Mapping[str, Mapping[str, Any] | None]) -> None:
        """Bulk upsert."""

    def query_disk(self, cell: str, k: int = 1) -> dict[str, dict[str, Any]] | None:
        """
        Return stored payloads for cells in the H3 grid disk.

        Returns None when the backend cannot evaluate the disk natively;
        callers should fall back to Python h3 + get_many.
        """
        return None

    @abstractmethod
    def close(self) -> None:
        """Release resources."""

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
