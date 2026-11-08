"""Store backends for h3lib."""

from h3lib.store.base import Store
from h3lib.store.duckdb_store import DuckDBStore
from h3lib.store.factory import create_store
from h3lib.store.sqlite_store import SQLiteStore

__all__ = [
    "Store",
    "SQLiteStore",
    "DuckDBStore",
    "create_store",
    "PostgresStore",
    "MySQLStore",
    "MongoStore",
]


def __getattr__(name: str):
    if name == "PostgresStore":
        from h3lib.store.postgres_store import PostgresStore

        return PostgresStore
    if name == "MySQLStore":
        from h3lib.store.mysql_store import MySQLStore

        return MySQLStore
    if name == "MongoStore":
        from h3lib.store.mongo_store import MongoStore

        return MongoStore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
