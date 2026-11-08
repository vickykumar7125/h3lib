# Measures & GeoJSON

```python
from h3lib import open_client

with open_client("sqlite") as client:
    cell = client.latlng_to_cell(37.7749, -122.4194, 9)

    area = client.cell_area(cell, unit="km^2")
    avg = client.average_hexagon_area(9, unit="km^2")
    n = client.get_num_cells(0)           # 122 at res 0
    res0 = client.get_res0_cells()
    pents = client.get_pentagons(5)

    geo = client.cells_to_geo([cell])     # GeoJSON-like geometry dict
```

Edge length helpers:

```python
from h3lib import average_hexagon_edge_length, edge_length

edge = client.directed_edges(cell)[0]
print(edge_length(edge, unit="km"))
print(average_hexagon_edge_length(9, unit="km"))
```

Supported area units follow h3-py (`km^2`, `m^2`, …).
