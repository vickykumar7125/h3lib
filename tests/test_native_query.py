"""Tests for DB-native H3 disk queries."""

from h3lib import create_store, open_client


def test_sqlite_query_disk_via_udfs():
    store = create_store("sqlite")
    origin = store.query_sql("SELECT h3_latlng_to_cell(37.7749, -122.4194, 9)")[0][0]
    store.put(origin, {"origin": True})
    # Put one neighbor so disk query can hit it.
    import json

    neighbors = json.loads(store.query_sql("SELECT h3_grid_disk(?, 1)", (origin,))[0][0])
    for i, cell in enumerate(neighbors):
        store.put(cell, {"i": i})
    found = store.query_disk(origin, 1)
    assert found is not None
    assert origin in found
    assert len(found) == len(neighbors)
    store.close()


def test_duckdb_native_query_disk():
    store = create_store("duckdb", enable_h3=True, require_h3=False)
    if not store.h3_extension_loaded:
        store.close()
        return
    origin = store.query_cells_sql(
        "SELECT h3_h3_to_string(h3_latlng_to_cell(37.7749, -122.4194, 9))"
    )[0][0]
    disk = store.query_cells_sql("SELECT UNNEST(h3_grid_disk(?, 1))", [origin])
    for i, (cell,) in enumerate(disk):
        store.put(str(cell), {"i": i})
    found = store.query_disk(origin, 1)
    assert found is not None
    assert origin in found
    assert len(found) >= 1
    store.close()


def test_client_prefer_db_duckdb():
    client = open_client("duckdb", enable_h3=True, prefer_db=True)
    if not client.supports_native_h3:
        client.close()
        return
    cell = client.put((37.7749, -122.4194), {"city": "SF"}, resolution=9)
    for n in client.grid_disk(cell, 1):
        client.put(n, {"n": n})
    hits = client.query_disk(cell, 1)
    assert cell in hits
    assert client.extension_status is not None
    client.close()
