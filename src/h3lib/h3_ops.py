"""Thin wrappers around the Uber h3 library."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

import h3


def latlng_to_cell(lat: float, lng: float, resolution: int) -> str:
    return h3.latlng_to_cell(lat, lng, resolution)


def cell_to_latlng(cell: str) -> tuple[float, float]:
    lat, lng = h3.cell_to_latlng(cell)
    return float(lat), float(lng)


def grid_disk(cell: str, k: int = 1) -> list[str]:
    return list(h3.grid_disk(cell, k))


def polygon_to_cells(
    polygon: Sequence[Sequence[float]] | dict[str, Any],
    resolution: int,
) -> list[str]:
    """Convert a ring [[lat, lng], ...] or GeoJSON-like polygon to H3 cells."""
    if isinstance(polygon, dict):
        # Prefer h3shape path for GeoJSON-like dicts (h3 v4).
        if hasattr(h3, "geo_to_h3shape") and hasattr(h3, "h3shape_to_cells"):
            shape = h3.geo_to_h3shape(polygon)
            return list(h3.h3shape_to_cells(shape, resolution))
        return list(h3.polygon_to_cells(polygon, resolution))

    # Outer ring as lat/lng pairs -> LatLngPoly when available.
    coords = [(float(lat), float(lng)) for lat, lng in polygon]
    if hasattr(h3, "LatLngPoly"):
        return list(h3.polygon_to_cells(h3.LatLngPoly(coords), resolution))

    if coords and coords[0] != coords[-1]:
        coords = list(coords) + [coords[0]]
    geo = {
        "type": "Polygon",
        "coordinates": [[[lng, lat] for lat, lng in coords]],
    }
    if hasattr(h3, "geo_to_h3shape") and hasattr(h3, "h3shape_to_cells"):
        return list(h3.h3shape_to_cells(h3.geo_to_h3shape(geo), resolution))
    return list(h3.polygon_to_cells(geo, resolution))


def ensure_cell(
    cell_or_point: str | tuple[float, float] | list[float],
    resolution: int | None = None,
) -> str:
    """Normalize a cell id or (lat, lng) point into a validated H3 cell string."""
    from h3lib.exceptions import IndexError_

    if isinstance(cell_or_point, str):
        if not h3.is_valid_cell(cell_or_point):
            raise IndexError_(f"Invalid H3 cell: {cell_or_point!r}")
        return cell_or_point
    if len(cell_or_point) != 2:
        raise IndexError_("point must be (lat, lng)")
    if resolution is None:
        raise IndexError_("resolution is required when passing a lat/lng point")
    lat, lng = float(cell_or_point[0]), float(cell_or_point[1])
    return latlng_to_cell(lat, lng, resolution)


def cells_from_iterable(cells: Iterable[str]) -> list[str]:
    """Normalize an iterable of cell ids to strings (no validity check)."""
    return [str(c) for c in cells]
