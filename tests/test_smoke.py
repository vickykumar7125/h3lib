"""Basic smoke tests for default stores and cache policy."""

from h3lib import H3Client, create_cache, create_store, open_client


def test_sqlite_crud_and_disk_query():
    client = open_client("sqlite", cache=True)
    cell = client.put((37.7749, -122.4194), {"city": "SF"}, resolution=9)
    got = client.get(cell)
    assert got is not None and got["city"] == "SF"
    assert got.get("_h3_mode") == "cell"
    nearby = client.query_disk(cell, k=1)
    assert cell in nearby
    assert client.delete(cell) is True
    assert client.get(cell) is None
    client.close()


def test_duckdb_store():
    store = create_store("duckdb", path=":memory:")
    store.put("89283082803ffff", {"ok": True})
    assert store.get("89283082803ffff") == {"ok": True}
    store.close()


def test_cache_policy_memory_when_enabled_without_redis():
    cache = create_cache(enabled=True)
    assert cache is not None
    cache.set("abc", {"x": 1})
    assert cache.get("abc") == {"x": 1}
    cache.close()


def test_h3client_from_config_duckdb():
    client = H3Client.from_config(store="duckdb", cache_enabled=True)
    cell = client.latlng_to_cell(0.0, 0.0, 5)
    client.put(cell, {"n": 1})
    assert client.get(cell)["n"] == 1
    client.close()
