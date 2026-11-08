"""h3lib — H3 geospatial indexing SDK with pluggable stores and cache."""

from h3lib.analytics import aggregate_points, smooth_disk
from h3lib.cache import InMemoryCache, create_cache
from h3lib.client import H3Client, open_client
from h3lib.exceptions import (
    CacheError,
    ConfigurationError,
    ExtensionError,
    H3LibError,
    IndexError_,
    MissingDependencyError,
    StoreError,
)
from h3lib.h3_ops import (
    cell_to_latlng,
    grid_disk,
    latlng_to_cell,
    polygon_to_cells,
)
from h3lib.hierarchy import (
    cell_to_center_child,
    cell_to_children,
    cell_to_parent,
    compact_cells,
    uncompact_cells,
)
from h3lib.index_mode import (
    IndexInfo,
    IndexMode,
    describe_index,
    detect_mode,
    get_index_resolution,
    index_from_latlng,
    mode_metadata,
    related_indexes,
)
from h3lib.measures import (
    average_hexagon_area,
    average_hexagon_edge_length,
    cell_area,
    cells_to_geo,
    edge_length,
    get_num_cells,
    get_pentagons,
    get_res0_cells,
)
from h3lib.store import DuckDBStore, SQLiteStore, create_store
from h3lib.traversal import (
    cell_to_local_ij,
    grid_disk_distances,
    grid_distance,
    grid_path_cells,
    grid_ring,
    local_ij_to_cell,
)

__all__ = [
    "H3Client",
    "open_client",
    "IndexMode",
    "IndexInfo",
    "detect_mode",
    "describe_index",
    "get_index_resolution",
    "index_from_latlng",
    "mode_metadata",
    "related_indexes",
    "latlng_to_cell",
    "cell_to_latlng",
    "grid_disk",
    "polygon_to_cells",
    "cell_to_parent",
    "cell_to_children",
    "cell_to_center_child",
    "compact_cells",
    "uncompact_cells",
    "grid_ring",
    "grid_disk_distances",
    "grid_distance",
    "grid_path_cells",
    "cell_to_local_ij",
    "local_ij_to_cell",
    "cell_area",
    "average_hexagon_area",
    "average_hexagon_edge_length",
    "edge_length",
    "get_num_cells",
    "get_res0_cells",
    "get_pentagons",
    "cells_to_geo",
    "aggregate_points",
    "smooth_disk",
    "SQLiteStore",
    "DuckDBStore",
    "PostgresStore",
    "MySQLStore",
    "MongoStore",
    "create_store",
    "InMemoryCache",
    "RedisCache",
    "create_cache",
    "H3LibError",
    "MissingDependencyError",
    "StoreError",
    "CacheError",
    "ConfigurationError",
    "ExtensionError",
    "ExtensionStatus",
    "IndexError_",
]

__version__ = "0.1.0"


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
    if name == "RedisCache":
        from h3lib.cache.redis_cache import RedisCache

        return RedisCache
    if name == "ExtensionStatus":
        from h3lib.store.extensions import ExtensionStatus

        return ExtensionStatus
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
