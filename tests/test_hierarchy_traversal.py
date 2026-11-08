"""Hierarchy, traversal, and measures wrappers."""

import h3

from h3lib import (
    average_hexagon_area,
    cell_area,
    cell_to_center_child,
    cell_to_children,
    cell_to_local_ij,
    cell_to_parent,
    cells_to_geo,
    compact_cells,
    get_num_cells,
    get_pentagons,
    get_res0_cells,
    grid_disk_distances,
    grid_distance,
    grid_path_cells,
    grid_ring,
    latlng_to_cell,
    local_ij_to_cell,
    open_client,
    uncompact_cells,
)

SF = (37.7749, -122.4194)


def test_hierarchy_parent_children_compact():
    cell = latlng_to_cell(*SF, 9)
    parent = cell_to_parent(cell, 7)
    assert parent == h3.cell_to_parent(cell, 7)
    children = cell_to_children(parent, 9)
    assert cell in children
    center = cell_to_center_child(parent, 9)
    assert center == h3.cell_to_center_child(parent, 9)
    # compact_cells requires a homogeneous resolution set
    compacted = compact_cells(children)
    assert parent in compacted or set(compacted).issubset(set(children) | {parent})
    restored = uncompact_cells(compacted, 9)
    assert cell in restored


def test_traversal_ring_distance_path_ij():
    cell = latlng_to_cell(*SF, 9)
    ring = grid_ring(cell, 1)
    assert cell not in ring
    assert len(ring) >= 5
    distances = grid_disk_distances(cell, 1)
    assert (cell, 0) in distances
    assert all(d <= 1 for _, d in distances)
    neighbor = ring[0]
    assert grid_distance(cell, neighbor) == 1
    path = grid_path_cells(cell, neighbor)
    assert path[0] == cell and path[-1] == neighbor
    i, j = cell_to_local_ij(cell, neighbor)
    assert local_ij_to_cell(cell, i, j) == neighbor


def test_measures_area_and_lists():
    cell = latlng_to_cell(*SF, 9)
    area = cell_area(cell, unit="km^2")
    assert area > 0
    assert average_hexagon_area(9) > 0
    assert get_num_cells(0) == 122
    assert len(get_res0_cells()) == 122
    assert len(get_pentagons(5)) == 12
    geo = cells_to_geo([cell])
    assert geo


def test_client_surface_methods():
    with open_client("sqlite") as client:
        cell = client.latlng_to_cell(*SF, 9)
        assert client.cell_to_parent(cell, 7)
        assert client.grid_ring(cell, 1)
        assert client.cell_area(cell) > 0
