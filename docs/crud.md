# CRUD

## put / get / delete

```python
from h3lib import open_client

with open_client("sqlite") as client:
    # From point
    cell = client.put((37.7749, -122.4194), {"name": "SF"}, resolution=9)
    # From cell string
    client.put(cell, {"name": "SF", "n": 1})

    print(client.get(cell))
    assert client.delete(cell) is True
    assert client.get(cell) is None
```

## Bulk

```python
client.put_many({
    cell: {"n": 1},
    other: {"n": 2},
})
found = client.get_many([cell, other], strict=False)
# strict=True → raise IndexError_ on invalid / wrong-mode indexes
```

## Typed helpers

```python
cell = client.put_cell((37.77, -122.42), {"role": "cell"}, resolution=9)

edge = client.put_directed_edge(
    cell,
    destination=client.grid_disk(cell, 1)[1],
    payload={"role": "edge"},
)

vertex = client.put_vertex(cell=cell, vertex_num=0, payload={"corner": 0})
```

## put_topology

Stores a cell plus all related directed edges and vertices in **one** `put_many` batch:

```python
topo = client.put_topology((37.77, -122.42), {"place": "SF"}, resolution=9)
# {"cells": [...], "directed_edges": [...], "vertexes": [...]}
```

## Metadata stamping

When `stamp_mode_metadata=True` (default), each put adds:

| Key | Meaning |
|-----|---------|
| `_h3_index` | Index string |
| `_h3_mode` | `cell` / `directed_edge` / `vertex` |
| `_h3_resolution` | Resolution |
| `_h3_valid` | Validity flag |
| `_h3_lat` / `_h3_lng` | When known |
| `_h3_origin` / `_h3_destination` | For edges |

User payload keys starting with `_h3_` are overwritten while stamping is on.

```python
client = open_client("sqlite", stamp_mode_metadata=False)
```
