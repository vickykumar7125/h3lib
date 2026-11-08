"""H3 hierarchy helpers (thin wrappers around h3-py)."""

from __future__ import annotations

from collections.abc import Iterable

import h3

from h3lib.index_mode import IndexMode, ensure_index


def cell_to_parent(cell: str, parent_res: int) -> str:
    """
    Return the parent cell at parent_res.

    Note: H3 containment is logical (index hierarchy), not geometric.
    """
    cell = ensure_index(cell, IndexMode.CELL)
    return str(h3.cell_to_parent(cell, int(parent_res)))


def cell_to_children(cell: str, child_res: int) -> list[str]:
    cell = ensure_index(cell, IndexMode.CELL)
    return [str(c) for c in h3.cell_to_children(cell, int(child_res))]


def cell_to_center_child(cell: str, child_res: int) -> str:
    cell = ensure_index(cell, IndexMode.CELL)
    return str(h3.cell_to_center_child(cell, int(child_res)))


def compact_cells(cells: Iterable[str]) -> list[str]:
    validated = [ensure_index(c, IndexMode.CELL) for c in cells]
    return [str(c) for c in h3.compact_cells(validated)]


def uncompact_cells(cells: Iterable[str], res: int) -> list[str]:
    validated = [ensure_index(c, IndexMode.CELL) for c in cells]
    return [str(c) for c in h3.uncompact_cells(validated, int(res))]
