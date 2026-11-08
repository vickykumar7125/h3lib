# Traversal

```python
from h3lib import open_client

with open_client("sqlite") as client:
    cell = client.latlng_to_cell(37.7749, -122.4194, 9)

    disk = client.grid_disk(cell, k=1)              # closed disk (includes origin)
    ring = client.grid_ring(cell, k=1)              # hollow ring (excludes origin when k>0)
    pairs = client.grid_disk_distances(cell, k=2)   # [(cell, distance), ...]

    neighbor = ring[0]
    dist = client.grid_distance(cell, neighbor)
    path = client.grid_path_cells(cell, neighbor)

    i, j = client.cell_to_local_ij(cell, neighbor)
    back = client.local_ij_to_cell(cell, i, j)
```

## Rules

- `k` for `grid_disk_distances` / `smooth_disk` must be `>= 0` (negative raises `IndexError_`).
- `grid_disk` / `grid_ring` delegate to h3-py and reject invalid `k` the same way.

```python
from h3lib import grid_disk, grid_ring, grid_disk_distances, grid_distance, grid_path_cells
```
