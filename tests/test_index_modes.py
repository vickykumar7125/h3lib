"""Tests for H3 index modes: h3_index, cell, directed_edge, vertex."""

import pytest

from h3lib import (
    H3Client,
    IndexError_,
    IndexMode,
    describe_index,
    detect_mode,
    open_client,
    related_indexes,
)


def test_detect_modes():
    client = open_client("sqlite", index_mode="h3_index")
    cell = client.latlng_to_cell(37.7749, -122.4194, 9)
    edge = client.directed_edges(cell)[0]
    vertex = client.vertexes(cell)[0]
    assert detect_mode(cell) is IndexMode.CELL
    assert detect_mode(edge) is IndexMode.DIRECTED_EDGE
    assert detect_mode(vertex) is IndexMode.VERTEX
    client.close()


def test_describe_all_modes():
    cell = open_client("sqlite").latlng_to_cell(37.77, -122.42, 9)
    info = describe_index(cell)
    assert info.valid and info.mode is IndexMode.CELL and info.latlng

    edge = list(__import__("h3").origin_to_directed_edges(cell))[0]
    einfo = describe_index(edge)
    assert einfo.mode is IndexMode.DIRECTED_EDGE
    assert einfo.origin and einfo.destination and einfo.boundary

    vertex = __import__("h3").cell_to_vertex(cell, 0)
    vinfo = describe_index(vertex)
    assert vinfo.mode is IndexMode.VERTEX and vinfo.latlng


def test_default_h3_index_accepts_all():
    with open_client("sqlite", index_mode=IndexMode.H3_INDEX) as client:
        cell = client.put((37.77, -122.42), {"t": "cell"}, resolution=9)
        edge = client.directed_edges(cell)[0]
        vertex = client.vertexes(cell)[0]
        assert client.put(edge, {"t": "edge"}) == edge
        assert client.put(vertex, {"t": "vertex"}) == vertex
        assert client.get(cell)["_h3_mode"] == "cell"
        assert client.get(edge)["_h3_mode"] == "directed_edge"
        assert client.get(vertex)["_h3_mode"] == "vertex"


def test_cell_mode_rejects_edge():
    with open_client("sqlite", index_mode="cell") as client:
        cell = client.put((37.77, -122.42), {"ok": 1}, resolution=9)
        edge = client.directed_edges(cell)[0]
        with pytest.raises(IndexError_):
            client.put(edge, {"no": 1})


def test_put_topology_writes_edges_and_vertexes():
    with open_client("sqlite", index_mode="h3_index") as client:
        written = client.put_topology((37.77, -122.42), {"place": "SF"}, resolution=9)
        assert written["cells"]
        assert len(written["directed_edges"]) >= 5
        assert len(written["vertexes"]) >= 5
        edge_hits = client.query_edges_from_cell(written["cells"][0])
        assert edge_hits
        vert_hits = client.query_vertexes_from_cell(written["cells"][0])
        assert vert_hits


def test_related_indexes():
    cell = open_client("sqlite").latlng_to_cell(0, 0, 5)
    related = related_indexes(cell)
    assert cell in related["cells"]
    assert related["directed_edges"]
    assert related["vertexes"]


def test_index_from_latlng_modes():
    client = H3Client(index_mode="cell")
    cell = client.index_from_latlng(37.77, -122.42, 9, mode="cell")
    vertex = client.index_from_latlng(37.77, -122.42, 9, mode="vertex", vertex_num=1)
    neighbor = client.grid_disk(cell, 1)[1]
    edge = client.index_from_latlng(
        37.77, -122.42, 9, mode="directed_edge", neighbor=neighbor
    )
    assert detect_mode(cell) is IndexMode.CELL
    assert detect_mode(vertex) is IndexMode.VERTEX
    assert detect_mode(edge) is IndexMode.DIRECTED_EDGE
    with pytest.raises(IndexError_):
        client.index_from_latlng(37.77, -122.42, 9, mode="directed_edge")
