# Quickstart

## Minimal CRUD

```python
from h3lib import open_client

with open_client("sqlite") as client:
    cell = client.put((37.7749, -122.4194), {"name": "SF"}, resolution=9)
    print(client.get(cell))
    print(client.query_disk(cell, k=1))
    client.delete(cell)
```

## Hierarchy + traversal

```python
from h3lib import open_client

with open_client("sqlite") as client:
    cell = client.latlng_to_cell(37.7749, -122.4194, 9)
    parent = client.cell_to_parent(cell, 7)
    ring = client.grid_ring(cell, 1)
    print(parent, ring[:3], client.cell_area(cell))
```

## Analytics

```python
from h3lib import open_client

points = [
    (37.7749, -122.4194),
    (37.7750, -122.4195),
    (37.7748, -122.4193),
]
with open_client("sqlite") as client:
    agg = client.aggregate_points(points, resolution=8)
    smoothed = client.smooth_disk({c: v["weight"] for c, v in agg.items()}, k=1)
    print(agg)
    print(smoothed)
```

## DuckDB + native disk query

```python
from h3lib import open_client

with open_client("duckdb", enable_h3=True, prefer_db=True, cache=True) as client:
    cell = client.put((37.77, -122.42), {"ok": 1}, resolution=9)
    print(client.supports_native_h3)
    print(client.query_disk(cell, k=1))
```

## Redis cache

```python
from h3lib import open_client

client = open_client(
    "sqlite",
    cache=True,
    redis_url="redis://127.0.0.1:6379/0",
    cache_options={"prefix": "h3lib:"},
)
cell = client.put((37.77, -122.42), {"cached": True}, resolution=9)
assert client.cache.get(cell)["cached"] is True
client.close()
```

## Index modes

```python
from h3lib import IndexMode, open_client

with open_client("sqlite", index_mode=IndexMode.H3_INDEX) as client:
    cell = client.put_cell((37.77, -122.42), {"role": "cell"}, resolution=9)
    edge = client.put_directed_edge(
        cell,
        destination=client.grid_disk(cell, 1)[1],
        payload={"role": "edge"},
    )
    vertex = client.put_vertex(cell=cell, vertex_num=0, payload={"corner": 0})
    topo = client.put_topology((37.77, -122.42), {"place": "SF"}, resolution=9)
```

Continue with [Client & configuration](client.md) and [Stores](stores.md).
