# Spatial queries

## query_disk (stored subset)

Returns payloads for **stored** neighbors in the H3 disk — not empty cells.

```python
hits = client.query_disk(cell, k=1, prefer_db=True)
# {cell: payload, ...}  — only indexes present in store/cache
```

When `prefer_db=True` (default) and the store supports native H3
(`supports_native_h3`), the disk is expanded inside DuckDB / Postgres / SQLite UDFs.

## query_polygon

```python
ring = [
    (37.78, -122.43),
    (37.78, -122.40),
    (37.76, -122.40),
    (37.76, -122.43),
]
hits = client.query_polygon(ring, resolution=9)
```

Also accepts GeoJSON-like polygon dicts via `polygon_to_cells`.

## Edges / vertices from a cell

```python
edge_hits = client.query_edges_from_cell(cell)
vert_hits = client.query_vertexes_from_cell(cell)
```

## Raw SQL (trusted operators only)

```python
# DuckDB
rows = client.store.query_cells_sql("SELECT h3_latlng_to_cell(37.77, -122.42, 9)")

# Postgres / SQLite
rows = client.store.query_sql("SELECT ...", params)
```

!!! danger
    Do not pass untrusted SQL. Table names for SQL stores are identifier-validated;
    raw SQL helpers are not.
