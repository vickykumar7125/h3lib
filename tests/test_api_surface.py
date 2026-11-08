"""Broader API / edge-case coverage for public helpers and client methods."""

import pytest

from h3lib import (
    IndexError_,
    IndexMode,
    average_hexagon_edge_length,
    cell_to_local_ij,
    cells_to_geo,
    compact_cells,
    describe_index,
    edge_length,
    get_index_resolution,
    grid_distance,
    grid_path_cells,
    local_ij_to_cell,
    open_client,
    related_indexes,
    uncompact_cells,
)
from h3lib.h3_ops import cells_from_iterable, ensure_cell
from h3lib.index_mode import indexes_from_sequence as idxs

SF = (37.7749, -122.4194)


def test_measures_edge_helpers():
    with open_client("sqlite") as client:
        cell = client.latlng_to_cell(*SF, 9)
        edge = client.directed_edges(cell)[0]
        assert edge_length(edge, unit="km") > 0
        assert average_hexagon_edge_length(9, unit="km") > 0
        assert get_index_resolution(edge) == 9


def test_client_hierarchy_traversal_geo():
    with open_client("sqlite") as client:
        cell = client.latlng_to_cell(*SF, 9)
        parent = client.cell_to_parent(cell, 7)
        children = client.cell_to_children(parent, 9)
        assert cell in children
        compacted = compact_cells(children)
        restored = uncompact_cells(compacted, 9)
        assert cell in restored
        neighbor = client.grid_ring(cell, 1)[0]
        assert grid_distance(cell, neighbor) == 1
        assert grid_path_cells(cell, neighbor)[0] == cell
        i, j = cell_to_local_ij(cell, neighbor)
        assert local_ij_to_cell(cell, i, j) == neighbor
        geo = cells_to_geo([cell])
        assert geo
        assert client.cells_to_geo([cell])
        info = describe_index(cell)
        assert info.valid
        related = related_indexes(cell)
        assert related["cells"] == [cell]


def test_related_indexes_edge_and_vertex():
    with open_client("sqlite") as client:
        cell = client.latlng_to_cell(*SF, 9)
        edge = client.directed_edges(cell)[0]
        vertex = client.vertexes(cell)[0]
        erel = related_indexes(edge)
        assert edge in erel["directed_edges"]
        assert len(erel["cells"]) == 2
        vrel = related_indexes(vertex)
        assert vrel["vertexes"] == [vertex]
        with pytest.raises(IndexError_):
            related_indexes("not-an-index")


def test_indexes_from_sequence_and_ensure_cell_point():
    with open_client("sqlite") as client:
        cell = client.latlng_to_cell(*SF, 9)
        assert idxs([cell], IndexMode.CELL) == [cell]
        assert cells_from_iterable([cell]) == [cell]
        assert ensure_cell(SF, resolution=9) == cell
        with pytest.raises(IndexError_):
            ensure_cell((1.0,), resolution=9)


def test_client_put_cell_vertex_and_query_helpers():
    with open_client("sqlite", cache=True) as client:
        cell = client.put_cell(SF, {"role": "c"}, resolution=9)
        vertex = client.put_vertex(cell=cell, vertex_num=0, payload={"v": 1})
        assert client.get(vertex)["v"] == 1
        assert client.query_vertexes_from_cell(cell)
        edge = client.put_directed_edge(cell, destination=client.grid_disk(cell, 1)[1])
        assert client.get(edge)
        assert client.query_edges_from_cell(cell)
        assert client.detect_mode(cell) is IndexMode.CELL
        assert client.describe(cell).valid
        assert client.related(cell)["cells"]
        assert client.average_hexagon_area(9) > 0
        assert client.get_num_cells(0) == 122
        assert len(client.get_res0_cells()) == 122
        assert len(client.get_pentagons(5)) == 12
