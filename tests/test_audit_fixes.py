"""Regression tests for continuous-audit defect fixes."""

from unittest.mock import MagicMock

import pytest

from h3lib import (
    ConfigurationError,
    IndexError_,
    IndexMode,
    create_cache,
    get_index_resolution,
    grid_disk_distances,
    latlng_to_cell,
    mode_metadata,
    open_client,
    smooth_disk,
)
from h3lib.analytics import aggregate_points
from h3lib.cache.redis_cache import RedisCache
from h3lib.h3_ops import ensure_cell
from h3lib.index_mode import get_index_resolution as gir


def test_grid_disk_distances_rejects_negative_k():
    cell = latlng_to_cell(37.77, -122.42, 9)
    with pytest.raises(IndexError_):
        grid_disk_distances(cell, -1)
    assert grid_disk_distances(cell, 0) == [(cell, 0)]


def test_smooth_disk_rejects_negative_k_and_subset_avg():
    cell = latlng_to_cell(37.77, -122.42, 9)
    with pytest.raises(IndexError_):
        smooth_disk({cell: 1.0}, k=-1)
    # Subset semantics: only present neighbors count.
    ring = open_client("sqlite").grid_ring(cell, 1)
    values = {cell: 10.0, ring[0]: 2.0}
    smoothed = smooth_disk(values, k=1)
    assert smoothed[cell] == pytest.approx((10.0 + 2.0) / 2.0)


def test_get_index_resolution_rejects_invalid():
    with pytest.raises(IndexError_):
        get_index_resolution("deadbeef")
    with pytest.raises(IndexError_):
        gir("not-an-index")
    cell = latlng_to_cell(0, 0, 5)
    assert get_index_resolution(cell) == 5


def test_mode_metadata_invalid_is_unknown():
    meta = mode_metadata("not-valid", IndexMode.CELL)
    assert meta["_h3_valid"] is False
    assert meta["_h3_mode"] == "unknown"


def test_aggregate_points_missing_keys():
    with pytest.raises(ValueError, match="lat"):
        aggregate_points([{"lat": 1.0}], 5)


def test_ensure_cell_raises_index_error():
    with pytest.raises(IndexError_):
        ensure_cell("nope")


def test_open_client_rejects_unknown_kwargs():
    with pytest.raises(ConfigurationError, match="Unknown open_client"):
        open_client("sqlite", bogus=1)


def test_put_directed_edge_positional_destination_hint():
    with open_client("sqlite") as client:
        cell = client.latlng_to_cell(37.77, -122.42, 9)
        dest = client.grid_disk(cell, 1)[1]
        with pytest.raises(IndexError_, match="destination="):
            client.put_directed_edge(cell, dest)


def test_create_cache_memory_backend_overrides_redis_url():
    cache = create_cache(enabled=True, backend="memory", redis_url="redis://localhost:6379/0")
    assert cache is not None
    from h3lib.cache.memory import InMemoryCache

    assert isinstance(cache, InMemoryCache)
    cache.close()


def test_redis_close_does_not_close_injected_client():
    pytest.importorskip("redis")
    client = MagicMock()
    cache = RedisCache(client=client, prefix="h3lib-audit:")
    cache.close()
    client.close.assert_not_called()


def test_duckdb_delete_rowcount_miss():
    from h3lib import create_store

    store = create_store("duckdb", enable_h3=False)
    assert store.delete("89283082803ffff") is False
    store.put("89283082803ffff", {"ok": 1})
    assert store.delete("89283082803ffff") is True
    store.close()


def test_memory_cache_thread_safe_basic():
    from h3lib.cache.memory import InMemoryCache

    cache = InMemoryCache()
    cache.set_many({"a": {"n": 1}, "b": {"n": 2}})
    assert cache.get_many(["a", "b"]) == {"a": {"n": 1}, "b": {"n": 2}}
    cache.clear()
    assert cache.get("a") is None
