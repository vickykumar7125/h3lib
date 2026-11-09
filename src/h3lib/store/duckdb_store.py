"""DuckDB store backend (default) with optional H3 extension."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import duckdb

from h3lib._util import dumps_payload, loads_payload
from h3lib.store.base import Store
from h3lib.store.extensions import ExtensionStatus, enable_duckdb_extensions

_SCHEMA = """
CREATE TABLE IF NOT EXISTS h3_cells (
    cell VARCHAR PRIMARY KEY,
    payload VARCHAR NOT NULL
);
"""


class DuckDBStore(Store):
    def __init__(
        self,
        path: str | Path = ":memory:",
        *,
        enable_h3: bool | None = None,
        load_h3_extension: bool | None = None,
        enable_spatial: bool = False,
        require_h3: bool = False,
    ) -> None:
        """
        Create a DuckDB-backed store.

        enable_h3 / load_h3_extension:
          When True (default), INSTALL/LOAD the community H3 extension.
        require_h3:
          When True, raise ExtensionError if H3 cannot be enabled.
        """
        self.path = str(path)
        self._conn = duckdb.connect(self.path)

        # load_h3_extension kept for backward compatibility
        if enable_h3 is None:
            enable_h3 = True if load_h3_extension is None else bool(load_h3_extension)

        self.extension_status: ExtensionStatus = enable_duckdb_extensions(
            self._conn,
            enable_h3=enable_h3,
            enable_spatial=enable_spatial,
            require_h3=require_h3,
        )
        self.h3_extension_loaded = bool(self.extension_status.enabled.get("h3"))
        self._conn.execute(_SCHEMA)

    def put(self, cell: str, payload: Mapping[str, Any] | None = None) -> None:
        self._conn.execute(
            """
            INSERT INTO h3_cells (cell, payload) VALUES (?, ?)
            ON CONFLICT (cell) DO UPDATE SET payload = excluded.payload
            """,
            [cell, dumps_payload(payload)],
        )

    def get(self, cell: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT payload FROM h3_cells WHERE cell = ?",
            [cell],
        ).fetchone()
        if row is None:
            return None
        return loads_payload(row[0])

    def delete(self, cell: str) -> bool:
        # DuckDB's Python cursor often leaves rowcount unset/0 after DELETE;
        # RETURNING is the portable way to detect whether a row was removed.
        row = self._conn.execute(
            "DELETE FROM h3_cells WHERE cell = ? RETURNING cell",
            [cell],
        ).fetchone()
        return row is not None

    def get_many(self, cells: Iterable[str]) -> dict[str, dict[str, Any]]:
        cell_list = list(cells)
        if not cell_list:
            return {}
        placeholders = ",".join("?" for _ in cell_list)
        rows = self._conn.execute(
            f"SELECT cell, payload FROM h3_cells WHERE cell IN ({placeholders})",
            cell_list,
        ).fetchall()
        out: dict[str, dict[str, Any]] = {}
        for cell, payload in rows:
            loaded = loads_payload(payload)
            if loaded is not None:
                out[cell] = loaded
        return out

    def put_many(self, items: Mapping[str, Mapping[str, Any] | None]) -> None:
        rows = [(cell, dumps_payload(payload)) for cell, payload in items.items()]
        if not rows:
            return
        self._conn.executemany(
            """
            INSERT INTO h3_cells (cell, payload) VALUES (?, ?)
            ON CONFLICT (cell) DO UPDATE SET payload = excluded.payload
            """,
            rows,
        )

    @property
    def supports_native_h3(self) -> bool:
        return self.h3_extension_loaded

    def query_disk(self, cell: str, k: int = 1) -> dict[str, dict[str, Any]] | None:
        """
        Return stored cells in the H3 disk (stored-subset, not full enumeration).
        """
        if not self.h3_extension_loaded:
            return None
        rows = self._conn.execute(
            """
            SELECT c.cell, c.payload
            FROM h3_cells AS c
            INNER JOIN (
                SELECT UNNEST(h3_grid_disk(?, ?)) AS cell
            ) AS d ON c.cell = d.cell
            """,
            [cell, int(k)],
        ).fetchall()
        out: dict[str, dict[str, Any]] = {}
        for cell_id, payload in rows:
            loaded = loads_payload(payload)
            if loaded is not None:
                out[str(cell_id)] = loaded
        return out

    def query_cells_sql(self, sql: str, params: list[Any] | None = None) -> list[Any]:
        """
        Run SQL (useful when the DuckDB H3 extension is loaded).

        Trusted-operator escape hatch — do not pass untrusted SQL.
        """
        return self._conn.execute(sql, params or []).fetchall()

    def close(self) -> None:
        self._conn.close()
