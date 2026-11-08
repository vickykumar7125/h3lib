"""Unified H3 client with store + optional cache + index modes."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from h3lib import analytics, h3_ops, hierarchy, measures, traversal
from h3lib.cache.base import Cache
from h3lib.cache.factory import create_cache
from h3lib.exceptions import ConfigurationError, IndexError_
from h3lib.index_mode import (
    IndexInfo,
    IndexMode,
    cell_directed_edges,
    cell_to_vertex_index,
    cell_vertexes,
    cells_to_edge,
    describe_index,
    detect_mode,
    edge_to_cells,
    ensure_index,
    filter_indexes_by_mode,
    index_from_latlng,
    mode_metadata,
    related_indexes,
)
from h3lib.store.base import Store
from h3lib.store.extensions import ExtensionStatus
from h3lib.store.factory import create_store


class H3Client:
    """
    High-level API:

    - Index modes: h3_index (default), cell, directed_edge, vertex
    - H3 helpers + edge/vertex constructors
    - CRUD against a pluggable store
    - Optional cache (Redis if provided, else in-memory)
    - prefer_db: use in-DB H3 when available
    """

    def __init__(
        self,
        store: Store | None = None,
        cache: Cache | None = None,
        *,
        default_resolution: int = 9,
        cache_ttl: int | None = None,
        prefer_db: bool = True,
        index_mode: IndexMode | str = IndexMode.H3_INDEX,
        stamp_mode_metadata: bool = True,
    ) -> None:
        self.store = store or create_store("sqlite")
        self.cache = cache
        self.default_resolution = default_resolution
        self.cache_ttl = cache_ttl
        self.prefer_db = prefer_db
        self.index_mode = IndexMode.parse(index_mode)
        self.stamp_mode_metadata = stamp_mode_metadata

    @property
    def extension_status(self) -> ExtensionStatus | None:
        return getattr(self.store, "extension_status", None)

    @property
    def supports_native_h3(self) -> bool:
        return bool(getattr(self.store, "supports_native_h3", False))

    @classmethod
    def from_config(
        cls,
        *,
        store: str = "sqlite",
        store_options: Mapping[str, Any] | None = None,
        cache_enabled: bool = False,
        redis_url: str | None = None,
        redis_client: Any | None = None,
        cache_backend: str | None = None,
        cache_options: Mapping[str, Any] | None = None,
        default_resolution: int = 9,
        cache_ttl: int | None = None,
        prefer_db: bool = True,
        index_mode: IndexMode | str = IndexMode.H3_INDEX,
        stamp_mode_metadata: bool = True,
    ) -> H3Client:
        store_backend = create_store(store, **dict(store_options or {}))
        cache_backend_obj = create_cache(
            enabled=cache_enabled,
            redis_url=redis_url,
            redis_client=redis_client,
            backend=cache_backend,
            **dict(cache_options or {}),
        )
        return cls(
            store=store_backend,
            cache=cache_backend_obj,
            default_resolution=default_resolution,
            cache_ttl=cache_ttl,
            prefer_db=prefer_db,
            index_mode=index_mode,
            stamp_mode_metadata=stamp_mode_metadata,
        )

    # --- H3 helpers -----------------------------------------------------

    def latlng_to_cell(self, lat: float, lng: float, resolution: int | None = None) -> str:
        return h3_ops.latlng_to_cell(lat, lng, resolution or self.default_resolution)

    def cell_to_latlng(self, cell: str) -> tuple[float, float]:
        return h3_ops.cell_to_latlng(cell)

    def grid_disk(self, cell: str, k: int = 1) -> list[str]:
        return h3_ops.grid_disk(ensure_index(cell, IndexMode.CELL), k)

    def polygon_to_cells(
        self,
        polygon: Sequence[Sequence[float]] | dict[str, Any],
        resolution: int | None = None,
    ) -> list[str]:
        return h3_ops.polygon_to_cells(polygon, resolution or self.default_resolution)

    def detect_mode(self, index: str) -> IndexMode | None:
        return detect_mode(index)

    def describe(self, index: str) -> IndexInfo:
        return describe_index(index)

    def related(self, index: str, **kwargs: Any) -> dict[str, Any]:
        return related_indexes(index, **kwargs)

    def index_from_latlng(
        self,
        lat: float,
        lng: float,
        resolution: int | None = None,
        *,
        mode: IndexMode | str | None = None,
        vertex_num: int = 0,
        neighbor: str | None = None,
    ) -> str:
        return index_from_latlng(
            lat,
            lng,
            resolution or self.default_resolution,
            IndexMode.parse(mode) if mode is not None else self.index_mode,
            vertex_num=vertex_num,
            neighbor=neighbor,
        )

    def directed_edges(self, cell: str) -> list[str]:
        return cell_directed_edges(cell)

    def vertexes(self, cell: str) -> list[str]:
        return cell_vertexes(cell)

    def cells_to_edge(self, origin: str, destination: str) -> str:
        return cells_to_edge(origin, destination)

    def edge_to_cells(self, edge: str) -> tuple[str, str]:
        return edge_to_cells(edge)

    def cell_to_vertex(self, cell: str, vertex_num: int) -> str:
        return cell_to_vertex_index(cell, vertex_num)

    # --- Hierarchy / traversal / measures --------------------------------

    def cell_to_parent(self, cell: str, parent_res: int) -> str:
        return hierarchy.cell_to_parent(cell, parent_res)

    def cell_to_children(self, cell: str, child_res: int) -> list[str]:
        return hierarchy.cell_to_children(cell, child_res)

    def cell_to_center_child(self, cell: str, child_res: int) -> str:
        return hierarchy.cell_to_center_child(cell, child_res)

    def compact_cells(self, cells: Iterable[str]) -> list[str]:
        return hierarchy.compact_cells(cells)

    def uncompact_cells(self, cells: Iterable[str], res: int) -> list[str]:
        return hierarchy.uncompact_cells(cells, res)

    def grid_ring(self, cell: str, k: int = 1) -> list[str]:
        return traversal.grid_ring(cell, k)

    def grid_disk_distances(self, cell: str, k: int = 1) -> list[tuple[str, int]]:
        return traversal.grid_disk_distances(cell, k)

    def grid_distance(self, origin: str, destination: str) -> int:
        return traversal.grid_distance(origin, destination)

    def grid_path_cells(self, origin: str, destination: str) -> list[str]:
        return traversal.grid_path_cells(origin, destination)

    def cell_to_local_ij(self, origin: str, cell: str) -> tuple[int, int]:
        return traversal.cell_to_local_ij(origin, cell)

    def local_ij_to_cell(self, origin: str, i: int, j: int) -> str:
        return traversal.local_ij_to_cell(origin, i, j)

    def cell_area(self, cell: str, unit: str = "km^2") -> float:
        return measures.cell_area(cell, unit=unit)

    def average_hexagon_area(self, resolution: int, unit: str = "km^2") -> float:
        return measures.average_hexagon_area(resolution, unit=unit)

    def get_num_cells(self, resolution: int) -> int:
        return measures.get_num_cells(resolution)

    def get_res0_cells(self) -> list[str]:
        return measures.get_res0_cells()

    def get_pentagons(self, resolution: int) -> list[str]:
        return measures.get_pentagons(resolution)

    def cells_to_geo(self, cells: Sequence[str]) -> dict[str, Any]:
        return measures.cells_to_geo(list(cells))

    def aggregate_points(
        self,
        points: Iterable[Any],
        resolution: int | None = None,
        **kwargs: Any,
    ) -> dict[str, dict[str, Any]]:
        return analytics.aggregate_points(
            points,
            resolution if resolution is not None else self.default_resolution,
            **kwargs,
        )

    def smooth_disk(
        self,
        values: Mapping[str, Any],
        k: int = 1,
        **kwargs: Any,
    ) -> dict[str, float]:
        return analytics.smooth_disk(values, k, **kwargs)

    def _resolve_index(
        self,
        value: str | tuple[float, float] | list[float],
        *,
        resolution: int | None = None,
        mode: IndexMode | None = None,
        vertex_num: int = 0,
        neighbor: str | None = None,
    ) -> str:
        active = mode or self.index_mode
        if isinstance(value, str):
            return ensure_index(value, active)
        if len(value) != 2:
            raise IndexError_("point must be (lat, lng)")
        return index_from_latlng(
            float(value[0]),
            float(value[1]),
            resolution if resolution is not None else self.default_resolution,
            active,
            vertex_num=vertex_num,
            neighbor=neighbor,
        )

    def _prepare_payload(
        self,
        index: str,
        payload: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        data = dict(payload or {})
        if self.stamp_mode_metadata:
            data.update(mode_metadata(index, self.index_mode))
        return data

    # --- CRUD -----------------------------------------------------------

    def put(
        self,
        index_or_point: str | tuple[float, float] | list[float],
        payload: Mapping[str, Any] | None = None,
        *,
        resolution: int | None = None,
        mode: IndexMode | str | None = None,
        vertex_num: int = 0,
        neighbor: str | None = None,
    ) -> str:
        active = IndexMode.parse(mode) if mode is not None else self.index_mode
        index = self._resolve_index(
            index_or_point,
            resolution=resolution,
            mode=active,
            vertex_num=vertex_num,
            neighbor=neighbor,
        )
        data = self._prepare_payload(index, payload)
        self.store.put(index, data)
        if self.cache is not None:
            self.cache.set(index, data, ttl=self.cache_ttl)
        return index

    def put_cell(
        self,
        cell_or_point: str | tuple[float, float] | list[float],
        payload: Mapping[str, Any] | None = None,
        *,
        resolution: int | None = None,
    ) -> str:
        return self.put(cell_or_point, payload, resolution=resolution, mode=IndexMode.CELL)

    def put_directed_edge(
        self,
        edge_or_origin: str | tuple[float, float] | list[float],
        payload: Mapping[str, Any] | None = None,
        *,
        destination: str | None = None,
        resolution: int | None = None,
        neighbor: str | None = None,
    ) -> str:
        # Guard against positional (origin, destination) confusion.
        if (
            destination is None
            and isinstance(edge_or_origin, str)
            and isinstance(payload, str)
            and detect_mode(str(payload)) is IndexMode.CELL
        ):
            raise IndexError_(
                "put_directed_edge second positional argument is payload, "
                "not destination. Use destination=<cell>."
            )
        if destination is not None and isinstance(edge_or_origin, str):
            edge = cells_to_edge(edge_or_origin, destination)
            return self.put(edge, payload, mode=IndexMode.DIRECTED_EDGE)
        return self.put(
            edge_or_origin,
            payload,
            resolution=resolution,
            mode=IndexMode.DIRECTED_EDGE,
            neighbor=neighbor or destination,
        )

    def put_vertex(
        self,
        vertex_or_point: str | tuple[float, float] | list[float] | None = None,
        payload: Mapping[str, Any] | None = None,
        *,
        resolution: int | None = None,
        vertex_num: int = 0,
        cell: str | None = None,
    ) -> str:
        if cell is not None:
            vertex = cell_to_vertex_index(cell, vertex_num)
            return self.put(vertex, payload, mode=IndexMode.VERTEX)
        if vertex_or_point is None:
            raise IndexError_("Provide vertex_or_point or cell=...")
        return self.put(
            vertex_or_point,
            payload,
            resolution=resolution,
            mode=IndexMode.VERTEX,
            vertex_num=vertex_num,
        )

    def put_topology(
        self,
        cell_or_point: str | tuple[float, float] | list[float],
        payload: Mapping[str, Any] | None = None,
        *,
        resolution: int | None = None,
        include_edges: bool = True,
        include_vertexes: bool = True,
    ) -> dict[str, list[str]]:
        """
        Store a cell and optionally all related directed edges and vertexes.

        Uses a single put_many batch. Returns the indexes written, grouped by mode.
        """
        cell = self._resolve_index(
            cell_or_point,
            resolution=resolution,
            mode=IndexMode.CELL,
        )
        base = dict(payload or {})
        written = related_indexes(
            cell,
            include_edges=include_edges,
            include_vertexes=include_vertexes,
        )
        items: dict[str, dict[str, Any]] = {
            cell: {**base, "role": "cell"},
        }
        for edge in written["directed_edges"]:
            items[edge] = {**base, "role": "directed_edge"}
        for vertex in written["vertexes"]:
            items[vertex] = {**base, "role": "vertex"}
        self.put_many(items, mode=IndexMode.H3_INDEX)
        return {
            "cells": written["cells"],
            "directed_edges": written["directed_edges"],
            "vertexes": written["vertexes"],
        }

    def get(
        self,
        index_or_point: str | tuple[float, float] | list[float],
        *,
        resolution: int | None = None,
        mode: IndexMode | str | None = None,
    ) -> dict[str, Any] | None:
        active = IndexMode.parse(mode) if mode is not None else self.index_mode
        index = self._resolve_index(index_or_point, resolution=resolution, mode=active)
        if self.cache is not None:
            cached = self.cache.get(index)
            if cached is not None:
                return cached
        payload = self.store.get(index)
        if payload is not None and self.cache is not None:
            self.cache.set(index, payload, ttl=self.cache_ttl)
        return payload

    def delete(
        self,
        index_or_point: str | tuple[float, float] | list[float],
        *,
        resolution: int | None = None,
        mode: IndexMode | str | None = None,
    ) -> bool:
        active = IndexMode.parse(mode) if mode is not None else self.index_mode
        index = self._resolve_index(index_or_point, resolution=resolution, mode=active)
        deleted = self.store.delete(index)
        if self.cache is not None:
            self.cache.delete(index)
        return deleted

    def put_many(
        self,
        items: Mapping[str, Mapping[str, Any] | None],
        *,
        mode: IndexMode | str | None = None,
    ) -> None:
        active = IndexMode.parse(mode) if mode is not None else self.index_mode
        prepared: dict[str, dict[str, Any]] = {}
        for index, payload in items.items():
            idx = ensure_index(index, active)
            prepared[idx] = self._prepare_payload(idx, payload)
        self.store.put_many(prepared)
        if self.cache is not None:
            self.cache.set_many(prepared, ttl=self.cache_ttl)

    def get_many(
        self,
        indexes: Iterable[str],
        *,
        mode: IndexMode | str | None = None,
        strict: bool = False,
    ) -> dict[str, dict[str, Any]]:
        """
        Fetch many indexes.

        By default (strict=False), indexes that are invalid or wrong-mode are
        silently dropped. Pass strict=True to raise IndexError_ on the first
        invalid / mismatched index.
        """
        active = IndexMode.parse(mode) if mode is not None else self.index_mode
        if strict:
            cell_list = [ensure_index(i, active) for i in indexes]
        else:
            cell_list = filter_indexes_by_mode(indexes, active)
        if not cell_list:
            return {}

        found: dict[str, dict[str, Any]] = {}
        missing = cell_list

        if self.cache is not None:
            found.update(self.cache.get_many(cell_list))
            missing = [c for c in cell_list if c not in found]

        if missing:
            loaded = self.store.get_many(missing)
            found.update(loaded)
            if self.cache is not None and loaded:
                self.cache.set_many(loaded, ttl=self.cache_ttl)
        return found

    # --- Queries --------------------------------------------------------

    def query_disk(
        self,
        cell_or_point: str | tuple[float, float] | list[float],
        k: int = 1,
        *,
        resolution: int | None = None,
        prefer_db: bool | None = None,
    ) -> dict[str, dict[str, Any]]:
        """
        Return payloads for stored cells in the H3 grid disk of radius k.

        This is a stored-subset query: neighbors that are not present in the
        store (or cache) are omitted. It does not enumerate empty disk cells.
        """
        cell = self._resolve_index(cell_or_point, resolution=resolution, mode=IndexMode.CELL)
        use_db = self.prefer_db if prefer_db is None else prefer_db
        if use_db and self.supports_native_h3:
            native = self.store.query_disk(cell, k)
            if native is not None:
                if self.cache is not None and native:
                    self.cache.set_many(native, ttl=self.cache_ttl)
                return native
        neighbors = self.grid_disk(cell, k)
        return self.get_many(neighbors, mode=IndexMode.H3_INDEX)

    def query_polygon(
        self,
        polygon: Sequence[Sequence[float]] | dict[str, Any],
        *,
        resolution: int | None = None,
    ) -> dict[str, dict[str, Any]]:
        cells = self.polygon_to_cells(polygon, resolution)
        return self.get_many(cells, mode=IndexMode.CELL)

    def query_edges_from_cell(
        self,
        cell_or_point: str | tuple[float, float] | list[float],
        *,
        resolution: int | None = None,
    ) -> dict[str, dict[str, Any]]:
        cell = self._resolve_index(cell_or_point, resolution=resolution, mode=IndexMode.CELL)
        return self.get_many(self.directed_edges(cell), mode=IndexMode.DIRECTED_EDGE)

    def query_vertexes_from_cell(
        self,
        cell_or_point: str | tuple[float, float] | list[float],
        *,
        resolution: int | None = None,
    ) -> dict[str, dict[str, Any]]:
        cell = self._resolve_index(cell_or_point, resolution=resolution, mode=IndexMode.CELL)
        return self.get_many(self.vertexes(cell), mode=IndexMode.VERTEX)

    def close(self) -> None:
        self.store.close()
        if self.cache is not None:
            self.cache.close()

    def __enter__(self) -> H3Client:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def open_client(
    store: str = "sqlite",
    *,
    cache: bool = False,
    redis_url: str | None = None,
    **kwargs: Any,
) -> H3Client:
    """Convenience constructor matching the documented cache / index-mode policy."""
    if store not in {
        "sqlite",
        "sqlite3",
        "duckdb",
        "duck",
        "postgres",
        "postgresql",
        "pg",
        "mysql",
        "mongo",
        "mongodb",
    }:
        raise ConfigurationError(f"Unknown store '{store}'")
    store_options = dict(kwargs.pop("store_options", None) or {})
    for key in (
        "path",
        "dsn",
        "uri",
        "database",
        "host",
        "port",
        "user",
        "password",
        "table",
        "collection",
        "enable_h3",
        "require_h3",
        "enable_spatial",
        "enable_postgis",
        "require_postgis",
        "enable_h3_postgis",
        "load_h3_extension",
        "register_h3_udfs",
        "enable_spatial_index",
        "enable_geo_index",
    ):
        if key in kwargs:
            store_options[key] = kwargs.pop(key)
    prefer_db = kwargs.pop("prefer_db", True)
    index_mode = kwargs.pop("index_mode", IndexMode.H3_INDEX)
    stamp_mode_metadata = kwargs.pop("stamp_mode_metadata", True)
    allowed = {
        "cache_backend",
        "cache_options",
        "cache_ttl",
        "default_resolution",
        "redis_client",
    }
    unknown = sorted(set(kwargs) - allowed)
    if unknown:
        raise ConfigurationError(
            f"Unknown open_client option(s): {', '.join(unknown)}"
        )
    return H3Client.from_config(
        store=store,
        store_options=store_options,
        cache_enabled=cache,
        redis_url=redis_url,
        prefer_db=prefer_db,
        index_mode=index_mode,
        stamp_mode_metadata=stamp_mode_metadata,
        **kwargs,
    )
