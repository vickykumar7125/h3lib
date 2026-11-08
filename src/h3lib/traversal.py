"""H3 grid traversal helpers (thin wrappers around h3-py)."""

from __future__ import annotations

import h3

from h3lib.index_mode import IndexMode, ensure_index


def grid_ring(cell: str, k: int = 1) -> list[str]:
    """Hollow ring of cells at exact grid distance k (excludes origin when k>0)."""
    cell = ensure_index(cell, IndexMode.CELL)
    return [str(c) for c in h3.grid_ring(cell, int(k))]


def grid_disk_distances(cell: str, k: int = 1) -> list[tuple[str, int]]:
    """
    Cells in the closed disk of radius k with their grid distance.

    h3-py does not expose gridDiskDistances; this builds rings 0..k.
    """
    from h3lib.exceptions import IndexError_

    cell = ensure_index(cell, IndexMode.CELL)
    k = int(k)
    if k < 0:
        raise IndexError_("grid disk distance k must be >= 0")
    out: list[tuple[str, int]] = [(cell, 0)]
    for dist in range(1, k + 1):
        for neighbor in h3.grid_ring(cell, dist):
            out.append((str(neighbor), dist))
    return out


def grid_distance(origin: str, destination: str) -> int:
    origin = ensure_index(origin, IndexMode.CELL)
    destination = ensure_index(destination, IndexMode.CELL)
    return int(h3.grid_distance(origin, destination))


def grid_path_cells(origin: str, destination: str) -> list[str]:
    origin = ensure_index(origin, IndexMode.CELL)
    destination = ensure_index(destination, IndexMode.CELL)
    return [str(c) for c in h3.grid_path_cells(origin, destination)]


def cell_to_local_ij(origin: str, cell: str) -> tuple[int, int]:
    origin = ensure_index(origin, IndexMode.CELL)
    cell = ensure_index(cell, IndexMode.CELL)
    i, j = h3.cell_to_local_ij(origin, cell)
    return int(i), int(j)


def local_ij_to_cell(origin: str, i: int, j: int) -> str:
    origin = ensure_index(origin, IndexMode.CELL)
    return str(h3.local_ij_to_cell(origin, int(i), int(j)))
