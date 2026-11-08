# Indexing & modes

## Lat/lng ↔ cell

```python
from h3lib import open_client

with open_client("sqlite") as client:
    cell = client.latlng_to_cell(37.7749, -122.4194, 9)
    lat, lng = client.cell_to_latlng(cell)
```

Module-level helpers:

```python
from h3lib import index_from_latlng, latlng_to_cell, cell_to_latlng, IndexMode

cell = latlng_to_cell(37.77, -122.42, 9)
cell = index_from_latlng(37.77, -122.42, 9, mode=IndexMode.CELL)
```

## Index modes

| Mode | Value | Accepts |
|------|-------|---------|
| H3 Index (default) | `h3_index` | Any valid H3 index |
| Cell | `cell` | Cells only |
| Directed edge | `directed_edge` | Directed edges only |
| Vertex | `vertex` | Vertices only |

```python
from h3lib import IndexMode, detect_mode, describe_index, open_client

client = open_client("sqlite", index_mode=IndexMode.H3_INDEX)
cell = client.put_cell((37.77, -122.42), {"n": 1}, resolution=9)
print(detect_mode(cell))          # IndexMode.CELL
print(describe_index(cell))       # IndexInfo: mode, res, latlng, details
```

## Directed edges & vertices

```python
cell = client.latlng_to_cell(37.77, -122.42, 9)
edges = client.directed_edges(cell)
verts = client.vertexes(cell)
edge = client.cells_to_edge(cell, client.grid_disk(cell, 1)[1])
origin, dest = client.edge_to_cells(edge)
vertex = client.cell_to_vertex(cell, 0)
```

### From lat/lng

```python
from h3lib import IndexMode, index_from_latlng

cell = index_from_latlng(37.77, -122.42, 9, mode=IndexMode.CELL)
vertex = index_from_latlng(37.77, -122.42, 9, mode=IndexMode.VERTEX, vertex_num=0)

# Directed edge REQUIRES neighbor= (destination cell)
neighbor = client.grid_disk(cell, 1)[1]
edge = index_from_latlng(
    37.77, -122.42, 9, mode=IndexMode.DIRECTED_EDGE, neighbor=neighbor
)
```

!!! warning "Positional footgun"
    `put_directed_edge(origin, destination)` is **wrong** — the second positional
    argument is `payload`. Use `destination=...`.

## Related topology

```python
from h3lib import related_indexes

related = related_indexes(cell)
# {"cells": [...], "directed_edges": [...], "vertexes": [...], ...}
```

## Resolution helper

```python
from h3lib import get_index_resolution

print(get_index_resolution(cell))   # works for cell / edge / vertex
# Invalid indexes raise IndexError_
```
