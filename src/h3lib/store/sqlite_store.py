"""SQLite store backend (default) with Python H3 UDFs (no native extension)."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import h3

from h3lib._util import dumps_payload, loads_payload
from h3lib.store.base import Store
from h3lib.store.extensions import ExtensionStatus, sqlite_extension_status


class SQLiteStore(Store):
    def __init__(
        self,
        path: str | Path = ":memory:",
        *,
        register_h3_udfs: bool = True,
    ) -> None:
        self.path = str(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS h3_cells (
                cell TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

        udfs_ok = False
        if register_h3_udfs:
            udfs_ok = self._register_h3_udfs()
        self.extension_status: ExtensionStatus = sqlite_extension_status(
            udfs_registered=udfs_ok
        )
        self.h3_extension_loaded = False  # no native SQLite H3 extension

    def _register_h3_udfs(self) -> bool:
        try:
            self._conn.create_function(
                "h3_latlng_to_cell",
                3,
                lambda lat, lng, res: h3.latlng_to_cell(float(lat), float(lng), int(res)),
            )
            self._conn.create_function(
                "h3_cell_to_latlng",
                1,
                lambda cell: json.dumps(list(h3.cell_to_latlng(str(cell)))),
            )
            self._conn.create_function(
                "h3_grid_disk",
                2,
                lambda cell, k: json.dumps(list(h3.grid_disk(str(cell), int(k)))),
            )
            self._conn.create_function(
                "h3_is_valid_cell",
                1,
                lambda cell: 1 if h3.is_valid_cell(str(cell)) else 0,
            )
            return True
        except Exception:
            return False

    def put(self, cell: str, payload: Mapping[str, Any] | None = None) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO h3_cells (cell, payload) VALUES (?, ?)",
            (cell, dumps_payload(payload)),
        )
        self._conn.commit()

    def get(self, cell: str) -> dict[str, Any] | None:
        cur = self._conn.execute(
            "SELECT payload FROM h3_cells WHERE cell = ?",
            (cell,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return loads_payload(row[0])

    def delete(self, cell: str) -> bool:
        cur = self._conn.execute("DELETE FROM h3_cells WHERE cell = ?", (cell,))
        self._conn.commit()
        return cur.rowcount > 0

    def get_many(self, cells: Iterable[str]) -> dict[str, dict[str, Any]]:
        cell_list = list(cells)
        if not cell_list:
            return {}
        placeholders = ",".join("?" for _ in cell_list)
        cur = self._conn.execute(
            f"SELECT cell, payload FROM h3_cells WHERE cell IN ({placeholders})",
            cell_list,
        )
        out: dict[str, dict[str, Any]] = {}
        for cell, payload in cur.fetchall():
            loaded = loads_payload(payload)
            if loaded is not None:
                out[cell] = loaded
        return out

    def put_many(self, items: Mapping[str, Mapping[str, Any] | None]) -> None:
        self._conn.executemany(
            "INSERT OR REPLACE INTO h3_cells (cell, payload) VALUES (?, ?)",
            [(cell, dumps_payload(payload)) for cell, payload in items.items()],
        )
        self._conn.commit()

    @property
    def supports_native_h3(self) -> bool:
        return bool(self.extension_status.enabled.get("python_h3_udfs"))

    def query_disk(self, cell: str, k: int = 1) -> dict[str, dict[str, Any]] | None:
        if not self.supports_native_h3:
            return None
        row = self._conn.execute(
            "SELECT h3_grid_disk(?, ?)",
            (cell, int(k)),
        ).fetchone()
        if not row or row[0] is None:
            return {}
        neighbors = json.loads(row[0])
        return self.get_many(neighbors)

    def query_sql(self, sql: str, params: tuple[Any, ...] | list[Any] | None = None) -> list[Any]:
        cur = self._conn.execute(sql, params or ())
        return list(cur.fetchall())

    def close(self) -> None:
        self._conn.close()
