"""Tests for H3 helper wrappers."""

import time

import pytest

from h3lib import MissingDependencyError, create_cache, create_store, open_client
from h3lib.h3_ops import cell_to_latlng, grid_disk, latlng_to_cell, polygon_to_cells


def test_latlng_roundtrip():
    cell = latlng_to_cell(37.7749, -122.4194, 9)
    lat, lng = cell_to_latlng(cell)
    assert abs(lat - 37.7749) < 0.01
    assert abs(lng - (-122.4194)) < 0.01


def test_grid_disk_includes_origin():
    cell = latlng_to_cell(37.7749, -122.4194, 9)
    disk = grid_disk(cell, 1)
    assert cell in disk
    assert len(disk) >= 7


def test_polygon_to_cells_ring():
    ring = [
        (37.78, -122.43),
        (37.78, -122.40),
        (37.76, -122.40),
        (37.76, -122.43),
    ]
    cells = polygon_to_cells(ring, 8)
    assert len(cells) > 0


def test_polygon_to_cells_geojson():
    geo = {
        "type": "Polygon",
        "coordinates": [
            [
                [-122.43, 37.78],
                [-122.40, 37.78],
                [-122.40, 37.76],
                [-122.43, 37.76],
                [-122.43, 37.78],
            ]
        ],
    }
    cells = polygon_to_cells(geo, 8)
    assert len(cells) > 0


def test_query_polygon_via_client():
    client = open_client("sqlite", cache=True)
    ring = [
        (37.78, -122.43),
        (37.78, -122.40),
        (37.76, -122.40),
        (37.76, -122.43),
    ]
    cells = client.polygon_to_cells(ring, resolution=9)
    assert cells
    client.put(cells[0], {"i": 0})
    found = client.query_polygon(ring, resolution=9)
    assert cells[0] in found
    client.close()


def test_memory_cache_ttl_expiry():
    cache = create_cache(enabled=True)
    assert cache is not None
    cache.set("c1", {"v": 1}, ttl=1)
    assert cache.get("c1") == {"v": 1}
    time.sleep(1.1)
    assert cache.get("c1") is None
    cache.close()


def test_missing_redis_dependency_message():
    # Force import path error by requesting redis without relying on installed redis.
    # If redis is installed in the env, skip this assertion path.
    try:
        import redis  # noqa: F401

        pytest.skip("redis is installed in this environment")
    except ImportError:
        pass

    with pytest.raises(MissingDependencyError):
        create_cache(enabled=True, redis_url="redis://localhost:6379/0")


def test_unknown_store_raises():
    from h3lib import ConfigurationError

    with pytest.raises(ConfigurationError):
        create_store("oracle")
