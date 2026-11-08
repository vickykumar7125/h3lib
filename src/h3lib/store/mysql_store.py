"""MySQL store backend (optional) — no native H3; spatial index fallback."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from h3lib._util import (
    dumps_payload,
    loads_payload,
    quote_ident_mysql,
    require_module,
    validate_sql_identifier,
)
from h3lib.store.base import Store
from h3lib.store.extensions import ExtensionStatus, mysql_extension_status


class MySQLStore(Store):
    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str,
        table: str = "h3_cells",
        enable_spatial_index: bool = True,
        **kwargs: Any,
    ) -> None:
        pymysql = require_module("pymysql", "mysql")
        validated = validate_sql_identifier(table)
        self._table = validated
        self._qtable = quote_ident_mysql(validated)
        self._spatial_enabled = False
        self._conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            autocommit=True,
            charset="utf8mb4",
            **kwargs,
        )
        spatial_ok = False
        with self._conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._qtable} (
                    cell VARCHAR(32) PRIMARY KEY,
                    payload JSON NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            if enable_spatial_index:
                spatial_ok = self._ensure_spatial_columns(cur)
                self._spatial_enabled = spatial_ok

        self.extension_status: ExtensionStatus = mysql_extension_status(
            spatial_index=spatial_ok
        )
        self.h3_extension_loaded = False

    def _ensure_spatial_columns(self, cur: Any) -> bool:
        """
        Add optional centroid POINT + SPATIAL INDEX.
        MySQL has no H3 extension; this aids geo lookups alongside cell PK.
        """
        try:
            cur.execute(f"SHOW COLUMNS FROM {self._qtable} LIKE 'centroid'")
            if cur.fetchone() is None:
                cur.execute(
                    f"ALTER TABLE {self._qtable} ADD COLUMN centroid POINT NULL"
                )
            # SPATIAL INDEX requires NOT NULL in older MySQL; try best-effort.
            index_ok = False
            try:
                idx = validate_sql_identifier(
                    f"idx_{self._table.replace('.', '_')}_centroid"
                )
                cur.execute(
                    f"CREATE SPATIAL INDEX {quote_ident_mysql(idx)} "
                    f"ON {self._qtable} (centroid)"
                )
                index_ok = True
            except Exception:
                # Index may already exist — treat as success if named index is present.
                try:
                    cur.execute(f"SHOW INDEX FROM {self._qtable}")
                    rows = cur.fetchall() or []
                    names = {str(r[2]) for r in rows if len(r) > 2}
                    idx_name = f"idx_{self._table.replace('.', '_')}_centroid"
                    index_ok = idx_name in names
                except Exception:
                    index_ok = False
            return index_ok
        except Exception:
            return False

    def _centroid_from_payload(
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
        centroid = self._centroid_from_payload(payload) if self._spatial_enabled else None
        with self._conn.cursor() as cur:
            if centroid is not None:
                lat, lng = centroid
                # MySQL geographic SRS 4326 expects POINT(latitude longitude).
                cur.execute(
                    f"""
                    INSERT INTO {self._qtable} (cell, payload, centroid)
                    VALUES (%s, CAST(%s AS JSON), ST_PointFromText(%s, 4326))
                    ON DUPLICATE KEY UPDATE
                      payload = VALUES(payload),
                      centroid = VALUES(centroid)
                    """,
                    (cell, raw, f"POINT({lat} {lng})"),
                )
            elif self._spatial_enabled:
                cur.execute(
                    f"""
                    INSERT INTO {self._qtable} (cell, payload, centroid)
                    VALUES (%s, CAST(%s AS JSON), NULL)
                    ON DUPLICATE KEY UPDATE
                      payload = VALUES(payload),
                      centroid = NULL
                    """,
                    (cell, raw),
                )
            else:
                cur.execute(
                    f"""
                    INSERT INTO {self._qtable} (cell, payload) VALUES (%s, CAST(%s AS JSON))
                    ON DUPLICATE KEY UPDATE payload = VALUES(payload)
                    """,
                    (cell, raw),
                )

    def get(self, cell: str) -> dict[str, Any] | None:
        with self._conn.cursor() as cur:
            cur.execute(
                f"SELECT CAST(payload AS CHAR) FROM {self._qtable} WHERE cell = %s",
                (cell,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return loads_payload(row[0])

    def delete(self, cell: str) -> bool:
        with self._conn.cursor() as cur:
            affected = cur.execute(
                f"DELETE FROM {self._qtable} WHERE cell = %s",
                (cell,),
            )
        return int(affected) > 0

    def get_many(self, cells: Iterable[str]) -> dict[str, dict[str, Any]]:
        cell_list = list(cells)
        if not cell_list:
            return {}
        placeholders = ",".join(["%s"] * len(cell_list))
        with self._conn.cursor() as cur:
            cur.execute(
                f"SELECT cell, CAST(payload AS CHAR) FROM {self._qtable} "
                f"WHERE cell IN ({placeholders})",
                cell_list,
            )
            rows = cur.fetchall()
        out: dict[str, dict[str, Any]] = {}
        for cell, payload in rows:
            loaded = loads_payload(payload)
            if loaded is not None:
                out[cell] = loaded
        return out

    def put_many(self, items: Mapping[str, Mapping[str, Any] | None]) -> None:
        if not items:
            return
        with self._conn.cursor() as cur:
            if self._spatial_enabled:
                rows = []
                for cell, payload in items.items():
                    raw = dumps_payload(payload)
                    centroid = self._centroid_from_payload(payload)
                    if centroid is not None:
                        lat, lng = centroid
                        rows.append((cell, raw, f"POINT({lat} {lng})"))
                    else:
                        rows.append((cell, raw, None))
                # Mix of NULL / POINT — use two paths for clarity.
                for cell, raw, wkt in rows:
                    if wkt is not None:
                        cur.execute(
                            f"""
                            INSERT INTO {self._qtable} (cell, payload, centroid)
                            VALUES (%s, CAST(%s AS JSON), ST_PointFromText(%s, 4326))
                            ON DUPLICATE KEY UPDATE
                              payload = VALUES(payload),
                              centroid = VALUES(centroid)
                            """,
                            (cell, raw, wkt),
                        )
                    else:
                        cur.execute(
                            f"""
                            INSERT INTO {self._qtable} (cell, payload, centroid)
                            VALUES (%s, CAST(%s AS JSON), NULL)
                            ON DUPLICATE KEY UPDATE
                              payload = VALUES(payload),
                              centroid = NULL
                            """,
                            (cell, raw),
                        )
            else:
                rows = [(cell, dumps_payload(payload)) for cell, payload in items.items()]
                cur.executemany(
                    f"""
                    INSERT INTO {self._qtable} (cell, payload) VALUES (%s, CAST(%s AS JSON))
                    ON DUPLICATE KEY UPDATE payload = VALUES(payload)
                    """,
                    rows,
                )

    def close(self) -> None:
        self._conn.close()
