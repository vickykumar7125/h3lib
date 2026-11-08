"""PostgreSQL store backend (optional) with PostGIS / h3-pg support."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from h3lib._util import (
    dumps_payload,
    loads_payload,
    quote_ident_pg,
    require_module,
    validate_sql_identifier,
)
from h3lib.store.base import Store
from h3lib.store.extensions import ExtensionStatus, enable_postgres_extensions


class PostgresStore(Store):
    def __init__(
        self,
        dsn: str,
        *,
        table: str = "h3_cells",
        enable_postgis: bool = True,
        enable_h3: bool = True,
        enable_h3_postgis: bool = True,
        require_postgis: bool = False,
        require_h3: bool = False,
    ) -> None:
        """
        Connect and ensure PostGIS / h3 extensions when requested.

        If the OS-level extension package is missing, ExtensionError (when
        required) or extension_status.messages explain how to install it.
        """
        psycopg = require_module("psycopg", "postgres")
        validated = validate_sql_identifier(table)
        self._table = validated
        self._qtable = quote_ident_pg(validated)
        self._conn = psycopg.connect(dsn)

        self.extension_status: ExtensionStatus = enable_postgres_extensions(
            self._conn,
            enable_postgis=enable_postgis,
            enable_h3=enable_h3,
            enable_h3_postgis=enable_h3_postgis,
            require_postgis=require_postgis,
            require_h3=require_h3,
        )
        self.postgis_enabled = bool(self.extension_status.enabled.get("postgis"))
        self.h3_extension_loaded = bool(self.extension_status.enabled.get("h3"))
        self.h3_postgis_enabled = bool(self.extension_status.enabled.get("h3_postgis"))
        # True when a writable (non-GENERATED) h3 column exists.
        self._h3_writable = False

        self._init_schema()

    def _init_schema(self) -> None:
        # Base table always available.
        self._conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._qtable} (
                cell TEXT PRIMARY KEY,
                payload JSONB NOT NULL
            );
            """
        )
        # When h3-pg is present, add typed h3index column for native operators/indexes.
        if self.h3_extension_loaded:
            try:
                self._conn.execute(
                    f"""
                    ALTER TABLE {self._qtable}
                    ADD COLUMN IF NOT EXISTS h3 h3index
                    GENERATED ALWAYS AS (cell::h3index) STORED
                    """
                )
            except Exception:
                # Older PG / h3 versions may not support generated columns this way.
                try:
                    self._conn.rollback()
                    self._conn.execute(
                        f"ALTER TABLE {self._qtable} ADD COLUMN IF NOT EXISTS h3 h3index"
                    )
                except Exception:
                    self._conn.rollback()
            self._h3_writable = self._detect_writable_h3_column()
            try:
                h3_idx = validate_sql_identifier(
                    f"idx_{self._table.replace('.', '_')}_h3"
                )
                self._conn.execute(
                    f"CREATE INDEX IF NOT EXISTS {quote_ident_pg(h3_idx)} "
                    f"ON {self._qtable} USING btree (h3)"
                )
            except Exception:
                self._conn.rollback()

        # Optional geography point for PostGIS distance queries (centroid filled by app).
        if self.postgis_enabled:
            try:
                self._conn.execute(
                    f"""
                    ALTER TABLE {self._qtable}
                    ADD COLUMN IF NOT EXISTS geom geography(Point, 4326)
                    """
                )
                geom_idx = validate_sql_identifier(
                    f"idx_{self._table.replace('.', '_')}_geom"
                )
                self._conn.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS {quote_ident_pg(geom_idx)}
                    ON {self._qtable} USING GIST (geom)
                    """
                )
            except Exception:
                self._conn.rollback()

        self._conn.commit()

    def _detect_writable_h3_column(self) -> bool:
        """Return True if column h3 exists and is not GENERATED ALWAYS."""
        try:
            # Resolve possibly schema-qualified table name.
            if "." in self._table:
                schema, table = self._table.split(".", 1)
            else:
                schema, table = "public", self._table
            cur = self._conn.execute(
                """
                SELECT is_generated
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND table_name = %s
                  AND column_name = 'h3'
                """,
                (schema, table),
            )
            row = cur.fetchone()
            if row is None:
                return False
            # 'ALWAYS' / 'NEVER' (SQL standard); treat anything else as writable.
            return str(row[0]).upper() != "ALWAYS"
        except Exception:
            try:
                self._conn.rollback()
            except Exception:
                pass
            return False

    def _geom_from_payload(
        self, payload: Mapping[str, Any] | None
    ) -> tuple[float, float] | None:
        data = dict(payload or {})
        lat = data.get("_h3_lat", data.get("lat"))
        lng = data.get("_h3_lng", data.get("lng"))
        if lat is None or lng is None:
            return None
        try:
            return float(lat), float(lng)
        except (TypeError, ValueError):
            return None

    def put(self, cell: str, payload: Mapping[str, Any] | None = None) -> None:
        raw = dumps_payload(payload)
        geom = self._geom_from_payload(payload) if self.postgis_enabled else None

        if self.h3_extension_loaded and self._h3_writable:
            if geom is not None and self.postgis_enabled:
                lat, lng = geom
                self._conn.execute(
                    f"""
                    INSERT INTO {self._qtable} (cell, payload, h3, geom)
                    VALUES (%s, %s::jsonb, %s::h3index,
                            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography)
                    ON CONFLICT (cell) DO UPDATE
                      SET payload = EXCLUDED.payload,
                          h3 = EXCLUDED.h3,
                          geom = EXCLUDED.geom
                    """,
                    (cell, raw, cell, lng, lat),
                )
            else:
                self._conn.execute(
                    f"""
                    INSERT INTO {self._qtable} (cell, payload, h3)
                    VALUES (%s, %s::jsonb, %s::h3index)
                    ON CONFLICT (cell) DO UPDATE
                      SET payload = EXCLUDED.payload,
                          h3 = EXCLUDED.h3
                    """,
                    (cell, raw, cell),
                )
            self._conn.commit()
            return

        if geom is not None and self.postgis_enabled:
            lat, lng = geom
            self._conn.execute(
                f"""
                INSERT INTO {self._qtable} (cell, payload, geom)
                VALUES (%s, %s::jsonb,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography)
                ON CONFLICT (cell) DO UPDATE
                  SET payload = EXCLUDED.payload,
                      geom = EXCLUDED.geom
                """,
                (cell, raw, lng, lat),
            )
        else:
            self._conn.execute(
                f"""
                INSERT INTO {self._qtable} (cell, payload) VALUES (%s, %s::jsonb)
                ON CONFLICT (cell) DO UPDATE SET payload = EXCLUDED.payload
                """,
                (cell, raw),
            )
        self._conn.commit()

    def get(self, cell: str) -> dict[str, Any] | None:
        cur = self._conn.execute(
            f"SELECT payload::text FROM {self._qtable} WHERE cell = %s",
            (cell,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return loads_payload(row[0])

    def delete(self, cell: str) -> bool:
        cur = self._conn.execute(
            f"DELETE FROM {self._qtable} WHERE cell = %s",
            (cell,),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def get_many(self, cells: Iterable[str]) -> dict[str, dict[str, Any]]:
        cell_list = list(cells)
        if not cell_list:
            return {}
        cur = self._conn.execute(
            f"SELECT cell, payload::text FROM {self._qtable} WHERE cell = ANY(%s)",
            (cell_list,),
        )
        out: dict[str, dict[str, Any]] = {}
        for cell, payload in cur.fetchall():
            loaded = loads_payload(payload)
            if loaded is not None:
                out[cell] = loaded
        return out

    def put_many(self, items: Mapping[str, Mapping[str, Any] | None]) -> None:
        if not items:
            return
        if self.h3_extension_loaded and self._h3_writable:
            rows = [
                (cell, dumps_payload(payload), cell) for cell, payload in items.items()
            ]
            with self._conn.cursor() as cur:
                cur.executemany(
                    f"""
                    INSERT INTO {self._qtable} (cell, payload, h3)
                    VALUES (%s, %s::jsonb, %s::h3index)
                    ON CONFLICT (cell) DO UPDATE
                      SET payload = EXCLUDED.payload,
                          h3 = EXCLUDED.h3
                    """,
                    rows,
                )
        else:
            rows = [(cell, dumps_payload(payload)) for cell, payload in items.items()]
            with self._conn.cursor() as cur:
                cur.executemany(
                    f"""
                    INSERT INTO {self._qtable} (cell, payload) VALUES (%s, %s::jsonb)
                    ON CONFLICT (cell) DO UPDATE SET payload = EXCLUDED.payload
                    """,
                    rows,
                )
        self._conn.commit()

    @property
    def supports_native_h3(self) -> bool:
        return self.h3_extension_loaded

    def query_disk(self, cell: str, k: int = 1) -> dict[str, dict[str, Any]] | None:
        if not self.h3_extension_loaded:
            return None
        cur = self._conn.execute(
            f"""
            SELECT t.cell, t.payload::text
            FROM {self._qtable} AS t
            JOIN h3_grid_disk(%s::h3index, %s) AS d(cell_idx)
              ON t.cell::h3index = d.cell_idx
            """,
            (cell, int(k)),
        )
        out: dict[str, dict[str, Any]] = {}
        for cell_id, payload in cur.fetchall():
            loaded = loads_payload(payload)
            if loaded is not None:
                out[str(cell_id)] = loaded
        return out

    def query_sql(self, sql: str, params: tuple[Any, ...] | list[Any] | None = None) -> list[Any]:
        """
        Run SQL leveraging PostGIS / h3-pg when enabled.

        Trusted-operator escape hatch — do not pass untrusted SQL.
        """
        cur = self._conn.execute(sql, params or ())
        return list(cur.fetchall())

    def close(self) -> None:
        self._conn.close()
