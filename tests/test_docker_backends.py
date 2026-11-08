"""Integration tests against docker-compose backends.

Requires:
  docker compose up -d
  pip install -e ".[all]"
"""

from __future__ import annotations

import os

import pytest

from h3lib import H3Client, create_cache, create_store, open_client

pytestmark = pytest.mark.integration

PG_DSN = os.getenv(
    "H3LIB_PG_DSN",
    "postgresql://h3lib:h3lib@127.0.0.1:5432/h3lib",
)
MYSQL_KWARGS = {
    "host": os.getenv("H3LIB_MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("H3LIB_MYSQL_PORT", "3306")),
    "user": os.getenv("H3LIB_MYSQL_USER", "h3lib"),
    "password": os.getenv("H3LIB_MYSQL_PASSWORD", "h3lib"),
    "database": os.getenv("H3LIB_MYSQL_DATABASE", "h3lib"),
}
MONGO_URI = os.getenv(
    "H3LIB_MONGO_URI",
    "mongodb://127.0.0.1:27017/?directConnection=true",
)
REDIS_URL = os.getenv("H3LIB_REDIS_URL", "redis://127.0.0.1:6379/0")

SF = (37.7749, -122.4194)


def _ping_or_skip(connect, label: str):
    try:
        connect()
    except Exception as exc:  # noqa: BLE001 — surface as skip for CI without docker
        pytest.skip(f"{label} not reachable: {exc}")


@pytest.fixture(scope="module")
def postgres_store():
    pytest.importorskip("psycopg")

    def connect():
        store = create_store(
            "postgres",
            dsn=PG_DSN,
            table="h3_cells_pg",
            enable_postgis=True,
            enable_h3=True,
            enable_h3_postgis=True,
            require_postgis=True,
            require_h3=True,
        )
        store.close()

    _ping_or_skip(connect, "postgres")
    store = create_store(
        "postgres",
        dsn=PG_DSN,
        table="h3_cells_pg",
        enable_postgis=True,
        enable_h3=True,
        enable_h3_postgis=True,
        require_postgis=True,
        require_h3=True,
    )
    yield store
    store.close()


@pytest.fixture(scope="module")
def mysql_store():
    pytest.importorskip("pymysql")

    def connect():
        store = create_store("mysql", table="h3_cells_it", **MYSQL_KWARGS)
        store.close()

    _ping_or_skip(connect, "mysql")
    store = create_store("mysql", table="h3_cells_it", **MYSQL_KWARGS)
    yield store
    store.close()


@pytest.fixture(scope="module")
def mongo_store():
    pytest.importorskip("pymongo")

    def connect():
        store = create_store(
            "mongo",
            uri=MONGO_URI,
            database="h3lib_it",
            collection="h3_cells_it",
        )
        store.close()

    _ping_or_skip(connect, "mongo")
    store = create_store(
        "mongo",
        uri=MONGO_URI,
        database="h3lib_it",
        collection="h3_cells_it",
    )
    yield store
    store.close()


@pytest.fixture(scope="module")
def redis_cache():
    pytest.importorskip("redis")

    def connect():
        cache = create_cache(
            enabled=True,
            redis_url=REDIS_URL,
            prefix="h3lib-it:",
        )
        assert cache is not None
        cache.set("__ping__", {"ok": True}, ttl=5)
        cache.close()

    _ping_or_skip(connect, "redis")
    cache = create_cache(enabled=True, redis_url=REDIS_URL, prefix="h3lib-it:")
    assert cache is not None
    yield cache
    cache.clear()
    cache.close()


def test_postgres_crud_and_bulk(postgres_store):
    assert postgres_store.postgis_enabled is True
    assert postgres_store.h3_extension_loaded is True
    assert postgres_store.extension_status.enabled.get("postgis") is True
    assert postgres_store.extension_status.enabled.get("h3") is True
    client = H3Client(store=postgres_store, stamp_mode_metadata=True, prefer_db=True)
    cell = client.put(SF, {"backend": "postgres"}, resolution=9)
    assert client.get(cell)["backend"] == "postgres"
    # geom should be populated from stamped lat/lng when PostGIS is enabled
    rows = postgres_store.query_sql(
        "SELECT ST_Y(geom::geometry), ST_X(geom::geometry) "
        "FROM h3_cells_pg WHERE cell = %s",
        (cell,),
    )
    assert rows and rows[0][0] is not None and rows[0][1] is not None
    assert abs(float(rows[0][0]) - 37.77) < 0.05
    assert abs(float(rows[0][1]) - (-122.42)) < 0.05
    # Native h3-pg disk query (stored-subset)
    disk = client.query_disk(cell, k=1, prefer_db=True)
    assert cell in disk
    # h3 SQL smoke
    h3_rows = postgres_store.query_sql(
        "SELECT h3_latlng_to_cell(POINT(%s, %s), 9)::text",
        (SF[1], SF[0]),  # POINT(x,y) = (lng, lat)
    )
    assert h3_rows and h3_rows[0][0]
    client.put_many({cell: {"backend": "postgres", "n": 2}})
    assert client.get(cell)["n"] == 2
    assert client.delete(cell) is True


def test_mysql_crud_and_centroid(mysql_store):
    client = H3Client(store=mysql_store, stamp_mode_metadata=True)
    cell = client.put(SF, {"backend": "mysql"}, resolution=9)
    got = client.get(cell)
    assert got is not None
    assert got["backend"] == "mysql"
    assert "_h3_lat" in got
    disk = client.query_disk(cell, k=1)
    assert cell in disk
    assert client.delete(cell) is True


def test_mongo_crud_and_bulk(mongo_store):
    client = H3Client(store=mongo_store, stamp_mode_metadata=True)
    cell = client.put(SF, {"backend": "mongo", "lat": SF[0], "lng": SF[1]}, resolution=9)
    assert client.get(cell)["backend"] == "mongo"
    other = client.latlng_to_cell(37.78, -122.41, 9)
    client.put_many({cell: {"backend": "mongo", "n": 1}, other: {"backend": "mongo", "n": 2}})
    many = client.get_many([cell, other])
    assert many[cell]["n"] == 1
    assert many[other]["n"] == 2
    assert client.delete(cell) is True
    assert client.delete(other) is True


def test_redis_cache_roundtrip(redis_cache):
    redis_cache.set("abc", {"x": 1})
    assert redis_cache.get("abc") == {"x": 1}
    redis_cache.set_many({"a": {"v": 1}, "b": {"v": 2}})
    assert redis_cache.get_many(["a", "b"]) == {"a": {"v": 1}, "b": {"v": 2}}
    redis_cache.delete("abc")
    assert redis_cache.get("abc") is None


def test_open_client_sqlite_with_redis_cache(redis_cache):
    # Redis is already validated; exercise open_client cache wiring against docker Redis.
    client = open_client(
        "sqlite",
        cache=True,
        redis_url=REDIS_URL,
        cache_options={"prefix": "h3lib-client-it:"},
    )
    try:
        cell = client.put(SF, {"via": "redis-cache"}, resolution=9)
        assert client.get(cell)["via"] == "redis-cache"
        assert client.cache is not None
        assert client.cache.get(cell)["via"] == "redis-cache"
    finally:
        if client.cache is not None:
            client.cache.clear()
        client.close()
