"""Store factory helpers."""

from __future__ import annotations

from typing import Any

from h3lib.exceptions import ConfigurationError
from h3lib.store.base import Store
from h3lib.store.duckdb_store import DuckDBStore
from h3lib.store.sqlite_store import SQLiteStore


def create_store(backend: str = "sqlite", **kwargs: Any) -> Store:
    """
    Create a store backend.

    Defaults:
      - sqlite (stdlib) — registers Python H3 UDFs
      - duckdb (core) — INSTALL/LOAD community H3 when enable_h3=True

    Optional extras:
      - postgres / postgresql — CREATE EXTENSION postgis / h3 / h3_postgis
      - mysql — no native H3; optional POINT + SPATIAL INDEX
      - mongo / mongodb — unique cell index + optional 2dsphere

    Extension kwargs (backend-specific):
      enable_h3, require_h3, enable_spatial, enable_postgis,
      require_postgis, enable_h3_postgis, register_h3_udfs,
      enable_spatial_index, enable_geo_index
    """
    name = backend.strip().lower()

    if name in {"sqlite", "sqlite3"}:
        return SQLiteStore(**kwargs)
    if name in {"duckdb", "duck"}:
        return DuckDBStore(**kwargs)
    if name in {"postgres", "postgresql", "pg"}:
        from h3lib.store.postgres_store import PostgresStore

        return PostgresStore(**kwargs)
    if name in {"mysql"}:
        from h3lib.store.mysql_store import MySQLStore

        return MySQLStore(**kwargs)
    if name in {"mongo", "mongodb"}:
        from h3lib.store.mongo_store import MongoStore

        return MongoStore(**kwargs)

    raise ConfigurationError(
        f"Unknown store backend '{backend}'. "
        "Choose: sqlite, duckdb, postgres, mysql, mongo"
    )
