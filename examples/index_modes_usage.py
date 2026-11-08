"""Demonstrate H3 Index / Cell / Directed Edge / Vertex modes."""

from h3lib import IndexMode, describe_index, open_client


def main() -> None:
    with open_client("sqlite", index_mode=IndexMode.H3_INDEX) as client:
        cell = client.put_cell((37.7749, -122.4194), {"name": "SF"}, resolution=9)
        print("cell:", cell, client.describe(cell).mode)

        edge = client.put_directed_edge(
            cell,
            {"kind": "outbound"},
            destination=client.grid_disk(cell, 1)[1],
        )
        print("edge:", edge, describe_index(edge))

        vertex = client.put_vertex(cell=cell, vertex_num=2, payload={"corner": 2})
        print("vertex:", vertex, client.get(vertex))

        topo = client.put_topology((40.7128, -74.0060), {"name": "NYC"}, resolution=8)
        print(
            "topology counts:",
            {k: len(v) for k, v in topo.items()},
        )
        print("edge hits:", len(client.query_edges_from_cell(topo["cells"][0])))
        print("vertex hits:", len(client.query_vertexes_from_cell(topo["cells"][0])))


if __name__ == "__main__":
    main()
