# Hierarchy

H3 parent/child relationships are **logical** (index hierarchy), not geometric containment.

```python
from h3lib import open_client

with open_client("sqlite") as client:
    cell = client.latlng_to_cell(37.7749, -122.4194, 9)

    parent = client.cell_to_parent(cell, 7)
    children = client.cell_to_children(parent, 9)
    center = client.cell_to_center_child(parent, 9)

    compacted = client.compact_cells(children)   # same-resolution set
    restored = client.uncompact_cells(compacted, 9)
```

Also available as module functions:

```python
from h3lib import (
    cell_to_parent,
    cell_to_children,
    cell_to_center_child,
    compact_cells,
    uncompact_cells,
)
```

!!! note
    `compact_cells` requires a homogeneous resolution set. Mixing resolutions raises an H3 error.
