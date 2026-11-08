"""Notebook-style analytics helpers (dataframe-agnostic)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from h3lib import h3_ops
from h3lib.traversal import grid_disk_distances


def aggregate_points(
    points: Iterable[Sequence[float] | Mapping[str, Any]],
    resolution: int,
    *,
    lat_key: str = "lat",
    lng_key: str = "lng",
    weight_key: str | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Bin lat/lng points into H3 cells.

    Accepts iterables of (lat, lng), (lat, lng, weight), or mapping records.
    Returns {cell: {"count": N, "weight": W}} (weight defaults to count).
    """
    counts: dict[str, int] = defaultdict(int)
    weights: dict[str, float] = defaultdict(float)

    for point in points:
        weight = 1.0
        if isinstance(point, Mapping):
            try:
                lat = float(point[lat_key])
                lng = float(point[lng_key])
            except KeyError as exc:
                raise ValueError(
                    f"point mapping must include '{lat_key}' and '{lng_key}'"
                ) from exc
            if weight_key is not None and weight_key in point:
                weight = float(point[weight_key])
        else:
            seq = list(point)
            if len(seq) < 2:
                raise ValueError("point must provide at least lat and lng")
            lat, lng = float(seq[0]), float(seq[1])
            if len(seq) >= 3:
                weight = float(seq[2])
        cell = h3_ops.latlng_to_cell(lat, lng, resolution)
        counts[cell] += 1
        weights[cell] += weight

    return {
        cell: {"count": counts[cell], "weight": weights[cell]}
        for cell in counts
    }


def smooth_disk(
    values: Mapping[str, float | int | Mapping[str, Any]],
    k: int = 1,
    *,
    value_key: str = "weight",
    include_center: bool = True,
) -> dict[str, float]:
    """
    Neighborhood average over each cell's grid disk of radius k.

    ``values`` may map cell -> numeric, or cell -> mapping with ``value_key``.
    Only neighbors present in ``values`` participate in the average
    (stored-subset semantics, matching ``query_disk``).
    """
    from h3lib.exceptions import IndexError_

    if int(k) < 0:
        raise IndexError_("smooth_disk k must be >= 0")

    numeric: dict[str, float] = {}
    for cell, raw in values.items():
        if isinstance(raw, Mapping):
            numeric[str(cell)] = float(raw.get(value_key, 0.0))
        else:
            numeric[str(cell)] = float(raw)

    out: dict[str, float] = {}
    for cell in numeric:
        total = 0.0
        n = 0
        for neighbor, dist in grid_disk_distances(cell, k):
            if not include_center and dist == 0:
                continue
            if neighbor not in numeric:
                continue
            total += numeric[neighbor]
            n += 1
        out[cell] = (total / n) if n else 0.0
    return out
