"""Milestone 1: metadata, SQL identifiers, topology bulk, cache safety."""

from unittest.mock import MagicMock, patch

import pytest

from h3lib import ConfigurationError, IndexMode, create_cache, open_client
from h3lib._util import validate_sql_identifier
from h3lib.client import H3Client
from h3lib.index_mode import describe_index, mode_metadata


def test_mode_metadata_avoids_topology_expansion():
    cell = open_client("sqlite").latlng_to_cell(37.7749, -122.4194, 9)
    with patch("h3lib.index_mode.h3.origin_to_directed_edges") as edges, patch(
        "h3lib.index_mode.h3.cell_to_vertexes"
    ) as verts:
        meta = mode_metadata(cell)
        edges.assert_not_called()
        verts.assert_not_called()
    assert meta["_h3_mode"] == "cell"
    assert meta["_h3_index"] == cell
    assert meta["_h3_lat"] is not None
    assert meta["_h3_lng"] is not None
    # describe still expands topology when requested explicitly
    info = describe_index(cell)
    assert info.details and "directed_edges" in info.details


def test_sql_identifier_rejects_injection():
    with pytest.raises(ConfigurationError):
        validate_sql_identifier("h3_cells; drop table x")
    with pytest.raises(ConfigurationError):
        validate_sql_identifier("x;delete")
    assert validate_sql_identifier("h3_cells") == "h3_cells"
    assert validate_sql_identifier("public.h3_cells") == "public.h3_cells"


def test_put_topology_uses_put_many():
    store = MagicMock()
    store.extension_status = None
    store.supports_native_h3 = False
    client = H3Client(store=store, index_mode=IndexMode.H3_INDEX)
    cell = client.latlng_to_cell(37.77, -122.42, 9)
    written = client.put_topology(cell, {"place": "SF"})
    store.put_many.assert_called_once()
    store.put.assert_not_called()
    args, _kwargs = store.put_many.call_args
    items = args[0]
    assert cell in items
    for edge in written["directed_edges"]:
        assert edge in items
    for vertex in written["vertexes"]:
        assert vertex in items


def test_create_cache_enabled_false_ignores_backend():
    assert create_cache(enabled=False, backend="memory") is None
    assert create_cache(enabled=False, backend="redis") is None
    assert create_cache(enabled=False) is None


def test_redis_empty_prefix_rejected():
    pytest.importorskip("redis")
    from h3lib.cache.redis_cache import RedisCache

    with pytest.raises(ConfigurationError):
        RedisCache(client=MagicMock(), prefix="")
