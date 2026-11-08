"""H3 indexing modes: H3 Index (default), Cell, Directed Edge, Vertex."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

import h3

from h3lib.exceptions import ConfigurationError, IndexError_


class IndexMode(str, Enum):
    """
    Indexing options supported by h3lib.

    H3_INDEX (default): accept any valid H3 index (cell, directed edge, or vertex).
    CELL: only cell-mode indexes.
    DIRECTED_EDGE: only directed-edge indexes.
    VERTEX: only vertex-mode indexes.
    """

    H3_INDEX = "h3_index"
    CELL = "cell"
    DIRECTED_EDGE = "directed_edge"
    VERTEX = "vertex"

    @classmethod
    def parse(cls, value: str | IndexMode | None) -> IndexMode:
        if value is None:
            return cls.H3_INDEX
        if isinstance(value, cls):
            return value
        key = str(value).strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "h3": cls.H3_INDEX,
            "h3index": cls.H3_INDEX,
            "h3_index": cls.H3_INDEX,
            "index": cls.H3_INDEX,
            "default": cls.H3_INDEX,
            "cell": cls.CELL,
            "cells": cls.CELL,
            "hex": cls.CELL,
            "hexagon": cls.CELL,
            "edge": cls.DIRECTED_EDGE,
            "edges": cls.DIRECTED_EDGE,
            "directed_edge": cls.DIRECTED_EDGE,
            "directededge": cls.DIRECTED_EDGE,
            "dir_edge": cls.DIRECTED_EDGE,
            "vertex": cls.VERTEX,
            "vertexes": cls.VERTEX,
            "vertices": cls.VERTEX,
        }
        if key not in aliases:
            raise ConfigurationError(
                f"Unknown index mode '{value}'. "
                "Choose: h3_index (default), cell, directed_edge, vertex"
            )
        return aliases[key]


@dataclass(frozen=True)
class IndexInfo:
    """Inspected metadata for an H3 index."""

    index: str
    mode: IndexMode
    resolution: int | None
    valid: bool
    latlng: tuple[float, float] | None = None
    origin: str | None = None
    destination: str | None = None
    boundary: list[tuple[float, float]] | None = None
    details: dict[str, Any] | None = None


def detect_mode(index: str) -> IndexMode | None:
    """Return the concrete mode for a valid index, or None if invalid."""
    if h3.is_valid_cell(index):
        return IndexMode.CELL
    if h3.is_valid_directed_edge(index):
        return IndexMode.DIRECTED_EDGE
    if h3.is_valid_vertex(index):
        return IndexMode.VERTEX
    return None


def get_index_resolution(index: str) -> int:
    """
    Resolution for any H3 index mode.

    h3-py get_resolution() only accepts cells; edges/vertices use bit layout
    (or the origin cell for directed edges).
    """
    if h3.is_valid_cell(index):
        return int(h3.get_resolution(index))
    if h3.is_valid_directed_edge(index):
        origin = h3.get_directed_edge_origin(index)
        return int(h3.get_resolution(origin))
    if h3.is_valid_vertex(index):
        value = int(h3.str_to_int(index))
        return int((value >> 52) & 0xF)
    raise IndexError_(f"Invalid H3 index: {index!r}")


def is_valid_for_mode(index: str, mode: IndexMode) -> bool:
    concrete = detect_mode(index)
    if concrete is None:
        return False
    if mode is IndexMode.H3_INDEX:
        return True
    return concrete is mode


def ensure_index(index: str, mode: IndexMode = IndexMode.H3_INDEX) -> str:
    """Validate and return index string for the configured mode."""
    idx = str(index)
    if not h3.is_valid_index(idx):
        raise IndexError_(f"Invalid H3 index: {idx!r}")
    if not is_valid_for_mode(idx, mode):
        actual = detect_mode(idx)
        raise IndexError_(
            f"H3 index {idx!r} is mode {actual.value if actual else 'unknown'}, "
            f"but client index_mode is {mode.value}"
        )
    return idx


def describe_index(index: str) -> IndexInfo:
    """Thoroughly describe a cell / directed-edge / vertex index."""
    idx = str(index)
    mode = detect_mode(idx)
    if mode is None:
        return IndexInfo(index=idx, mode=IndexMode.H3_INDEX, resolution=None, valid=False)

    resolution = get_index_resolution(idx)
    latlng = None
    origin = destination = None
    boundary = None
    details: dict[str, Any] = {"int": int(h3.str_to_int(idx))}

    if mode is IndexMode.CELL:
        lat, lng = h3.cell_to_latlng(idx)
        latlng = (float(lat), float(lng))
        details["is_pentagon"] = bool(h3.is_pentagon(idx))
        details["base_cell"] = int(h3.get_base_cell_number(idx))
        details["boundary"] = [
            (float(a), float(b)) for a, b in h3.cell_to_boundary(idx)
        ]
        boundary = details["boundary"]
        details["vertexes"] = list(h3.cell_to_vertexes(idx))
        details["directed_edges"] = list(h3.origin_to_directed_edges(idx))

    elif mode is IndexMode.DIRECTED_EDGE:
        origin, destination = h3.directed_edge_to_cells(idx)
        origin, destination = str(origin), str(destination)
        boundary = [(float(a), float(b)) for a, b in h3.directed_edge_to_boundary(idx)]
        # Midpoint approximation from boundary endpoints.
        if boundary:
            latlng = (
                sum(p[0] for p in boundary) / len(boundary),
                sum(p[1] for p in boundary) / len(boundary),
            )
        details["origin"] = origin
        details["destination"] = destination
        details["boundary"] = boundary

    elif mode is IndexMode.VERTEX:
        lat, lng = h3.vertex_to_latlng(idx)
        latlng = (float(lat), float(lng))

    return IndexInfo(
        index=idx,
        mode=mode,
        resolution=resolution,
        valid=True,
        latlng=latlng,
        origin=origin,
        destination=destination,
        boundary=boundary,
        details=details,
    )


# --- constructors -----------------------------------------------------------

def index_from_latlng(
    lat: float,
    lng: float,
    resolution: int,
    mode: IndexMode = IndexMode.CELL,
    *,
    vertex_num: int = 0,
    neighbor: str | None = None,
) -> str:
    """
    Build an index from a lat/lng according to mode.

    CELL / H3_INDEX -> cell containing the point
    VERTEX -> chosen vertex of that cell (vertex_num)
    DIRECTED_EDGE -> edge from cell to neighbor (neighbor required)
    """
    cell = h3.latlng_to_cell(lat, lng, resolution)
    if mode in (IndexMode.CELL, IndexMode.H3_INDEX):
        return str(cell)
    if mode is IndexMode.VERTEX:
        return str(h3.cell_to_vertex(cell, int(vertex_num)))
    if mode is IndexMode.DIRECTED_EDGE:
        if neighbor is None:
            raise IndexError_(
                "neighbor is required for directed_edge index_from_latlng "
                "(pass the destination cell)"
            )
        return str(h3.cells_to_directed_edge(cell, neighbor))
    raise ConfigurationError(f"Unsupported mode for latlng conversion: {mode}")


def cell_directed_edges(cell: str) -> list[str]:
    ensure_index(cell, IndexMode.CELL)
    return [str(e) for e in h3.origin_to_directed_edges(cell)]


def cell_vertexes(cell: str) -> list[str]:
    ensure_index(cell, IndexMode.CELL)
    return [str(v) for v in h3.cell_to_vertexes(cell) if v]


def cells_to_edge(origin: str, destination: str) -> str:
    ensure_index(origin, IndexMode.CELL)
    ensure_index(destination, IndexMode.CELL)
    return str(h3.cells_to_directed_edge(origin, destination))


def edge_to_cells(edge: str) -> tuple[str, str]:
    ensure_index(edge, IndexMode.DIRECTED_EDGE)
    origin, destination = h3.directed_edge_to_cells(edge)
    return str(origin), str(destination)


def cell_to_vertex_index(cell: str, vertex_num: int) -> str:
    ensure_index(cell, IndexMode.CELL)
    return str(h3.cell_to_vertex(cell, int(vertex_num)))


def related_indexes(
    index: str,
    *,
    include_edges: bool = True,
    include_vertexes: bool = True,
) -> dict[str, Any]:
    """
    Expand an index into related cell / edge / vertex indexes.

    Useful for storing or querying a full local topology.
    """
    info = describe_index(index)
    if not info.valid:
        raise IndexError_(f"Cannot expand invalid index: {index!r}")

    out: dict[str, Any] = {
        "index": info.index,
        "mode": info.mode.value,
        "resolution": info.resolution,
        "cells": [],
        "directed_edges": [],
        "vertexes": [],
    }

    if info.mode is IndexMode.CELL:
        out["cells"] = [info.index]
        if include_edges:
            out["directed_edges"] = cell_directed_edges(info.index)
        if include_vertexes:
            out["vertexes"] = cell_vertexes(info.index)
    elif info.mode is IndexMode.DIRECTED_EDGE:
        origin, destination = edge_to_cells(info.index)
        out["cells"] = [origin, destination]
        out["directed_edges"] = [info.index]
        if include_vertexes:
            # Vertices belonging to the origin cell (edge topology uses cell verts).
            out["vertexes"] = cell_vertexes(origin)
    elif info.mode is IndexMode.VERTEX:
        out["vertexes"] = [info.index]

    return out


def filter_indexes_by_mode(indexes: Iterable[str], mode: IndexMode) -> list[str]:
    return [str(i) for i in indexes if is_valid_for_mode(str(i), mode)]


def mode_metadata(index: str, mode: IndexMode | None = None) -> dict[str, Any]:
    """
    Lightweight payload metadata stamped onto stored records.

    Avoids full describe_index topology expansion (edges/vertexes/boundary lists).
    """
    idx = str(index)
    concrete = detect_mode(idx)
    valid = concrete is not None
    stamped_mode = concrete if valid else (mode or IndexMode.H3_INDEX)
    mode_value = (
        stamped_mode.value if isinstance(stamped_mode, IndexMode) else str(stamped_mode)
    )
    meta: dict[str, Any] = {
        "_h3_index": idx,
        "_h3_mode": mode_value,
        "_h3_resolution": get_index_resolution(idx) if valid else None,
        "_h3_valid": valid,
    }
    if not valid:
        meta["_h3_mode"] = "unknown"
        return meta

    if concrete is IndexMode.CELL:
        lat, lng = h3.cell_to_latlng(idx)
        meta["_h3_lat"] = float(lat)
        meta["_h3_lng"] = float(lng)
    elif concrete is IndexMode.DIRECTED_EDGE:
        origin, destination = h3.directed_edge_to_cells(idx)
        meta["_h3_origin"] = str(origin)
        meta["_h3_destination"] = str(destination)
        boundary = list(h3.directed_edge_to_boundary(idx))
        if boundary:
            meta["_h3_lat"] = sum(float(p[0]) for p in boundary) / len(boundary)
            meta["_h3_lng"] = sum(float(p[1]) for p in boundary) / len(boundary)
    elif concrete is IndexMode.VERTEX:
        lat, lng = h3.vertex_to_latlng(idx)
        meta["_h3_lat"] = float(lat)
        meta["_h3_lng"] = float(lng)
    return meta


def indexes_from_sequence(
    values: Sequence[str],
    mode: IndexMode = IndexMode.H3_INDEX,
) -> list[str]:
    return [ensure_index(v, mode) for v in values]
