"""Tests for DB extension bootstrap behavior."""

from h3lib import create_store, open_client


def test_duckdb_enable_h3_reports_status():
    store = create_store("duckdb", path=":memory:", enable_h3=True, require_h3=False)
    assert hasattr(store, "extension_status")
    assert "h3" in store.extension_status.enabled
    # May be True or False depending on network/community repo availability.
    assert isinstance(store.extension_status.enabled["h3"], bool)
    assert store.extension_status.messages
    store.close()


def test_duckdb_disable_h3():
    store = create_store("duckdb", path=":memory:", enable_h3=False)
    assert store.extension_status.enabled.get("h3") is False
    assert store.h3_extension_loaded is False
    store.close()


def test_sqlite_registers_h3_udfs():
    store = create_store("sqlite", path=":memory:", register_h3_udfs=True)
    assert store.extension_status.enabled.get("python_h3_udfs") is True
    rows = store.query_sql("SELECT h3_latlng_to_cell(37.7749, -122.4194, 9)")
    assert rows and rows[0][0]
    assert store.query_sql("SELECT h3_is_valid_cell(?)", (rows[0][0],))[0][0] == 1
    store.close()


def test_open_client_passes_extension_flags():
    client = open_client("sqlite", register_h3_udfs=True)
    assert client.store.extension_status.enabled.get("python_h3_udfs") is True
    client.close()
