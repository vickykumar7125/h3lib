# h3lib

[![CI](https://github.com/vickykumar7125/h3lib/actions/workflows/ci.yml/badge.svg)](https://github.com/vickykumar7125/h3lib/actions/workflows/ci.yml)
[![Python 3.10–3.14](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Python geospatial indexing SDK built on [Uber H3](https://h3geo.org/) (via [h3-py](https://github.com/uber/h3-py)), with pluggable storage backends and optional caching.

| | |
|---|---|
| **Docs / repo** | https://github.com/vickykumar7125/h3lib |
| **Clone (HTTPS)** | `git clone https://github.com/vickykumar7125/h3lib.git` |
| **Clone (SSH)** | `git clone git@github.com:vickykumar7125/h3lib.git` |
| **H3 reference** | https://h3geo.org/docs/ |
| **Requires** | Python ≥ 3.10 |

---

## Features

- **H3 helpers** — index, hierarchy, traversal, measures, GeoJSON export
- **Index modes** — `h3_index` (default), `cell`, `directed_edge`, `vertex`
- **CRUD** — `put` / `get` / `delete` / `put_many` / `get_many`, plus typed helpers and `put_topology`
- **Analytics** — `aggregate_points`, `smooth_disk` (no pandas required)
- **Spatial queries** — `query_disk`, `query_polygon`, `query_edges_from_cell`, `query_vertexes_from_cell`
- **Default stores** — SQLite (stdlib), DuckDB (community H3 extension)
- **Optional stores** — PostgreSQL (PostGIS + h3-pg), MySQL, MongoDB
- **Optional cache** — Redis if URL/client provided, otherwise in-memory
- **DB extensions** — auto `CREATE EXTENSION` / DuckDB `INSTALL` when possible; clear install guidance when packages are missing
- **CI** — Ubuntu / macOS / Windows × Python 3.10–3.14

---

## Quick setup — if you’ve done this kind of thing before

```bash
git clone https://github.com/vickykumar7125/h3lib.git
cd h3lib
conda create -n h3-lib python=3.11 -y
conda activate h3-lib
pip install -e ".[all]"
pytest -q -m "not integration"
```

**HTTPS**

```text
https://github.com/vickykumar7125/h3lib.git
```

**SSH**

```text
git@github.com:vickykumar7125/h3lib.git
```

### …or create a new repository on the command line

```bash
echo "# h3lib" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/vickykumar7125/h3lib.git
git push -u origin main
```

### …or push an existing repository from the command line

```bash
git remote add origin https://github.com/vickykumar7125/h3lib.git
git branch -M main
git push -u origin main
```

---

## Install

### Core (SQLite + DuckDB)

```bash
conda activate h3-lib   # or your venv
pip install -e .
```

### Optional extras

```bash
pip install -e ".[redis]"      # Redis cache
pip install -e ".[postgres]"   # psycopg (PostGIS + h3-pg server-side)
pip install -e ".[mysql]"      # PyMySQL
pip install -e ".[mongo]"      # pymongo
pip install -e ".[dev]"        # pytest, ruff, mypy
pip install -e ".[all]"        # everything above
```

---

## Quick start

```python
from h3lib import open_client

client = open_client("sqlite")  # in-memory SQLite, no cache

cell = client.put((37.7749, -122.4194), {"name": "SF"}, resolution=9)
print(client.get(cell))
print(client.query_disk(cell, k=1))
client.close()
```

Context-manager form:

```python
from h3lib import open_client

with open_client("sqlite", cache=True) as client:
    cell = client.put((37.77, -122.42), {"city": "SF"}, resolution=9)
    assert client.get(cell)["city"] == "SF"
```

---

## Usage patterns

### 1. Client construction

```python
from h3lib import H3Client, IndexMode, create_cache, create_store, open_client

# A) Convenience
client = open_client("sqlite", path="h3.db", cache=True, index_mode=IndexMode.H3_INDEX)

# B) Config / factory
client = H3Client.from_config(
    store="duckdb",
    store_options={"path": ":memory:", "enable_h3": True},
    cache_enabled=True,
    redis_url=None,          # → in-memory cache
    default_resolution=9,
    prefer_db=True,
    stamp_mode_metadata=True,
)

# C) Explicit store + cache
store = create_store("sqlite", path=":memory:")
cache = create_cache(enabled=True)  # InMemoryCache
client = H3Client(store=store, cache=cache, index_mode="cell")
```

`create_cache(enabled=False)` always returns `None` (even if `backend=` is set).  
`backend="memory"` wins over `redis_url` when both are provided.

### 2. Indexing: lat/lng ↔ cell

```python
cell = client.latlng_to_cell(37.7749, -122.4194, 9)
lat, lng = client.cell_to_latlng(cell)

# Or construct by index mode
from h3lib import index_from_latlng, IndexMode

cell = index_from_latlng(37.77, -122.42, 9, mode=IndexMode.CELL)
vertex = index_from_latlng(37.77, -122.42, 9, mode=IndexMode.VERTEX, vertex_num=0)
neighbor = client.grid_disk(cell, 1)[1]
edge = index_from_latlng(
    37.77, -122.42, 9, mode=IndexMode.DIRECTED_EDGE, neighbor=neighbor
)
```

Directed-edge-from-point **requires** `neighbor=` (destination cell).

### 3. CRUD

```python
# put accepts a cell string or (lat, lng)
cell = client.put((37.7749, -122.4194), {"name": "SF"}, resolution=9)
payload = client.get(cell)
client.put_many({cell: {"name": "SF", "n": 1}})
found = client.get_many([cell], strict=False)  # strict=True raises on bad indexes
client.delete(cell)
```

Typed helpers:

```python
cell = client.put_cell((37.77, -122.42), {"role": "cell"}, resolution=9)
edge = client.put_directed_edge(cell, destination=client.grid_disk(cell, 1)[1], payload={"role": "edge"})
vertex = client.put_vertex(cell=cell, vertex_num=0, payload={"corner": 0})

# Bulk: cell + all directed edges + vertexes (single put_many)
topo = client.put_topology((37.77, -122.42), {"place": "SF"}, resolution=9)
# topo == {"cells": [...], "directed_edges": [...], "vertexes": [...]}
```

By default, puts stamp `_h3_index`, `_h3_mode`, `_h3_resolution`, `_h3_valid`, and coordinates when known. Keys starting with `_h3_` in the user payload are overwritten when stamping is on (`stamp_mode_metadata=False` to disable).

### 4. Hierarchy

```python
parent = client.cell_to_parent(cell, 7)
children = client.cell_to_children(parent, 9)
center = client.cell_to_center_child(parent, 9)
compacted = client.compact_cells(children)
restored = client.uncompact_cells(compacted, 9)
```

H3 containment is **logical** (index hierarchy), not geometric.

### 5. Traversal

```python
disk = client.grid_disk(cell, k=1)                 # closed disk
ring = client.grid_ring(cell, k=1)                 # hollow ring (k>0 excludes origin)
pairs = client.grid_disk_distances(cell, k=2)      # [(cell, dist), ...]
dist = client.grid_distance(cell, ring[0])
path = client.grid_path_cells(cell, ring[0])
i, j = client.cell_to_local_ij(cell, ring[0])
back = client.local_ij_to_cell(cell, i, j)
```

`k` must be `>= 0` for disk-distance / smooth helpers.

### 6. Measures & GeoJSON

```python
area = client.cell_area(cell, unit="km^2")
avg = client.average_hexagon_area(9, unit="km^2")
n = client.get_num_cells(0)          # 122
res0 = client.get_res0_cells()
pents = client.get_pentagons(5)
geo = client.cells_to_geo([cell])    # GeoJSON-like geometry
```

### 7. Index modes & inspection

| Mode | Value | Behavior |
|------|-------|----------|
| **H3 Index** (default) | `h3_index` | Accept any valid H3 index |
| **Cell** | `cell` | Cells only |
| **Directed edge** | `directed_edge` | Unidirectional edges only |
| **Vertex** | `vertex` | Vertices only |

```python
from h3lib import IndexMode, describe_index, detect_mode, open_client, related_indexes

client = open_client("sqlite", index_mode=IndexMode.H3_INDEX)
print(detect_mode(cell))
print(describe_index(cell))       # mode, resolution, latlng, boundary, topology details
print(related_indexes(cell))      # cells / directed_edges / vertexes
print(client.directed_edges(cell))
print(client.vertexes(cell))
print(client.edge_to_cells(edge))
```

### 8. Spatial queries

```python
# Stored-subset disk: only neighbors that exist in the store/cache
hits = client.query_disk(cell, k=1, prefer_db=True)

ring = [
    (37.78, -122.43),
    (37.78, -122.40),
    (37.76, -122.40),
    (37.76, -122.43),
]
poly_hits = client.query_polygon(ring, resolution=9)
edge_hits = client.query_edges_from_cell(cell)
vert_hits = client.query_vertexes_from_cell(cell)
```

When DuckDB H3 / Postgres h3-pg / SQLite H3 UDFs are available, `prefer_db=True` (default) expands the disk inside the database.

### 9. Analytics

```python
agg = client.aggregate_points(
    [
        (37.7749, -122.4194),
        {"lat": 37.7750, "lng": -122.4195, "w": 2},
    ],
    resolution=8,
    weight_key="w",
)
# {cell: {"count": N, "weight": W}, ...}

smoothed = client.smooth_disk({c: v["weight"] for c, v in agg.items()}, k=1)
```

### 10. Stores

#### SQLite (default)

```python
client = open_client("sqlite", path="h3.db", register_h3_udfs=True)
```

Registers Python H3 UDFs (`h3_latlng_to_cell`, `h3_grid_disk`, …) for in-DB disk queries.

#### DuckDB

```python
client = open_client(
    "duckdb",
    path="h3.duckdb",
    enable_h3=True,
    require_h3=False,
    prefer_db=True,
    cache=True,
)
print(client.supports_native_h3)
print(client.store.extension_status.enabled)
```

#### PostgreSQL (PostGIS + h3-pg)

```python
from h3lib import H3Client

pg = H3Client.from_config(
    store="postgres",
    store_options={
        "dsn": "postgresql://h3lib:h3lib@127.0.0.1:5432/h3lib",
        "table": "h3_cells",
        "enable_postgis": True,
        "enable_h3": True,
        "enable_h3_postgis": True,
        "require_postgis": True,
        "require_h3": True,
    },
    prefer_db=True,
)
print(pg.store.extension_status.enabled)
# geom is filled from stamped lat/lng when PostGIS is on
```

#### MySQL

```python
client = H3Client.from_config(
    store="mysql",
    store_options={
        "host": "127.0.0.1",
        "port": 3306,
        "user": "h3lib",
        "password": "h3lib",
        "database": "h3lib",
        "enable_spatial_index": True,
    },
)
```

#### MongoDB

```python
client = H3Client.from_config(
    store="mongo",
    store_options={
        "uri": "mongodb://127.0.0.1:27017/?directConnection=true",
        "database": "h3lib",
        "collection": "h3_cells",
        "enable_geo_index": True,
    },
)
```

| Backend | Native H3 / spatial | Notes |
|---------|---------------------|-------|
| **DuckDB** | Community `h3` | `INSTALL h3 FROM community; LOAD h3;` |
| **PostgreSQL** | PostGIS + h3-pg | `CREATE EXTENSION` postgis / h3 / h3_postgis |
| **SQLite** | Python H3 UDFs | Cell PK |
| **MySQL** | Optional `POINT` centroid | H3 math in Python |
| **MongoDB** | Unique `cell` + optional `2dsphere` | H3 math in Python |

Force fail-fast with install guidance:

```python
from h3lib import ExtensionError, create_store

try:
    create_store("duckdb", enable_h3=True, require_h3=True)
except ExtensionError as e:
    print(e)
```

Table names for SQL stores are validated (`^[A-Za-z_][A-Za-z0-9_]*$` or `schema.table`). Raw `query_sql` / `query_cells_sql` are **trusted-operator** escape hatches.

### 11. Cache

```python
# Memory (default when cache=True and no Redis)
client = open_client("sqlite", cache=True)

# Redis (non-empty prefix required; empty prefix is rejected)
client = open_client(
    "sqlite",
    cache=True,
    redis_url="redis://127.0.0.1:6379/0",
    cache_options={"prefix": "h3lib:"},
)

from h3lib import create_cache
cache = create_cache(enabled=True, backend="memory")
cache = create_cache(enabled=True, redis_url="redis://127.0.0.1:6379/0", prefix="app:")
```

---

## Docker backends (local integration)

```bash
docker compose up -d --build
pip install -e ".[all]"
pytest -q -m integration
docker compose down
```

| Service | Image | Connect |
|---------|-------|---------|
| Postgres | `h3lib-postgis-h3:16` (PostGIS + **h3-pg**) | `postgresql://h3lib:h3lib@127.0.0.1:5432/h3lib` |
| MySQL | `mysql:8.4` | user/pass/db `h3lib` @ `127.0.0.1:3306` |
| MongoDB | `mongodb/mongodb-atlas-local` | `mongodb://127.0.0.1:27017/?directConnection=true` |
| Redis Stack | `redis/redis-stack` | `redis://127.0.0.1:6379/0` (no password); Insight `:8001` |

Ports bind to **127.0.0.1** only. Postgres Dockerfile: [`docker/postgres/Dockerfile`](docker/postgres/Dockerfile).

---

## Package layout

```text
src/h3lib/
  client.py          # H3Client / open_client
  h3_ops.py          # core H3 wrappers
  hierarchy.py       # parent / children / compact
  traversal.py       # ring / distance / path / local IJ
  measures.py        # area / counts / geo export
  analytics.py       # aggregate_points / soft neighborhood smooth
  index_mode.py      # IndexMode, describe, metadata stamping
  store/             # sqlite, duckdb, postgres, mysql, mongo
  cache/             # memory, redis + factory policy
examples/
tests/
docker/postgres/     # PostGIS + h3-pg image
```

---

## Examples

```bash
python examples/basic_usage.py
python examples/duckdb_usage.py
python examples/redis_cache_usage.py
python examples/postgres_extensions.py
python examples/index_modes_usage.py
python examples/analytics_usage.py
```

---

## Tests & CI

```bash
pip install -e ".[dev]"
pytest -q
pytest -q -m "not integration"   # default CI path
pytest -q -m integration         # needs docker compose
ruff check src tests
```

GitHub Actions runs on **ubuntu / macOS / windows** × **Python 3.10–3.14**.

---

## Documentation & links

| Resource | URL |
|----------|-----|
| **This project (GitHub)** | https://github.com/vickykumar7125/h3lib |
| Issues | https://github.com/vickykumar7125/h3lib/issues |
| Actions / CI | https://github.com/vickykumar7125/h3lib/actions |
| Uber H3 docs | https://h3geo.org/docs/ |
| h3-py | https://github.com/uber/h3-py |
| h3-pg | https://github.com/postgis/h3-pg |
| DuckDB H3 | https://duckdb.org/docs/extensions/h3 |
| PostGIS | https://postgis.net/ |

---

## License

MIT — see [LICENSE](LICENSE).
