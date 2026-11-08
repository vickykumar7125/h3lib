"""H3 area / edge / enumeration helpers (thin wrappers around h3-py)."""

from __future__ import annotations

import h3

from h3lib.index_mode import IndexMode, ensure_index


def cell_area(cell: str, unit: str = "km^2") -> float:
    cell = ensure_index(cell, IndexMode.CELL)
    return float(h3.cell_area(cell, unit=unit))


def average_hexagon_area(resolution: int, unit: str = "km^2") -> float:
    return float(h3.average_hexagon_area(int(resolution), unit=unit))


def average_hexagon_edge_length(resolution: int, unit: str = "km") -> float:
    return float(h3.average_hexagon_edge_length(int(resolution), unit=unit))


def edge_length(edge: str, unit: str = "km") -> float:
    edge = ensure_index(edge, IndexMode.DIRECTED_EDGE)
    return float(h3.edge_length(edge, unit=unit))


def get_num_cells(resolution: int) -> int:
    return int(h3.get_num_cells(int(resolution)))


def get_res0_cells() -> list[str]:
    return [str(c) for c in h3.get_res0_cells()]


def get_pentagons(resolution: int) -> list[str]:
    return [str(c) for c in h3.get_pentagons(int(resolution))]


def cells_to_geo(cells: list[str] | tuple[str, ...]) -> dict:
    """Return GeoJSON-like geometry for a collection of cells."""
    validated = [ensure_index(c, IndexMode.CELL) for c in cells]
    return h3.cells_to_geo(validated)
