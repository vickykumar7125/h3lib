# h3lib

[![CI](https://github.com/vickykumar7125/h3lib/actions/workflows/ci.yml/badge.svg)](https://github.com/vickykumar7125/h3lib/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-teal)](https://vickykumar7125.github.io/h3lib/)
[![Python 3.10–3.14](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/vickykumar7125/h3lib)](https://github.com/vickykumar7125/h3lib/releases)

Python geospatial indexing SDK built on [Uber H3](https://h3geo.org/) (via [h3-py](https://github.com/uber/h3-py)), with pluggable storage backends and optional caching.

| | |
|---|---|
| **Documentation website** | **https://vickykumar7125.github.io/h3lib/** |
| **Source** | https://github.com/vickykumar7125/h3lib |
| **Releases / wheels** | https://github.com/vickykumar7125/h3lib/releases |
| **Clone (HTTPS)** | `git clone https://github.com/vickykumar7125/h3lib.git` |
| **Clone (SSH)** | `git clone git@github.com:vickykumar7125/h3lib.git` |
| **H3 reference** | https://h3geo.org/docs/ |
| **Requires** | Python ≥ 3.10 |

> Full usage guides (install, client, indexing, CRUD, hierarchy, traversal, measures, queries, analytics, stores, cache, Docker) live on the **[documentation website](https://vickykumar7125.github.io/h3lib/)**.

---

## Features

- **H3 helpers** — index, hierarchy, traversal, measures, GeoJSON export
- **Index modes** — `h3_index` (default), `cell`, `directed_edge`, `vertex`
- **CRUD** — `put` / `get` / `delete` / `put_many` / `get_many`, typed helpers, `put_topology`
- **Analytics** — `aggregate_points`, `smooth_disk` (no pandas required)
- **Spatial queries** — `query_disk`, `query_polygon`, `query_edges_from_cell`, `query_vertexes_from_cell`
- **Default stores** — SQLite (stdlib), DuckDB (community H3 extension)
- **Optional stores** — PostgreSQL (PostGIS + h3-pg), MySQL, MongoDB
- **Optional cache** — Redis if URL/client provided, otherwise in-memory
- **DB extensions** — auto `CREATE EXTENSION` / DuckDB `INSTALL` when possible
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

**HTTPS:** `https://github.com/vickykumar7125/h3lib.git`  
**SSH:** `git@github.com:vickykumar7125/h3lib.git`

Install a release wheel:

```bash
pip install https://github.com/vickykumar7125/h3lib/releases/download/v0.1.0/h3lib-0.1.0-py3-none-any.whl
```

---

## Install

```bash
conda activate h3-lib   # or your venv
pip install -e .

pip install -e ".[redis]"      # Redis cache
pip install -e ".[postgres]"   # PostgreSQL / PostGIS / h3-pg
pip install -e ".[mysql]"
pip install -e ".[mongo]"
pip install -e ".[dev]"        # pytest, ruff, mypy
pip install -e ".[all]"
```

Docs site locally:

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

---

## Quick start

```python
from h3lib import open_client

with open_client("sqlite") as client:
    cell = client.put((37.7749, -122.4194), {"name": "SF"}, resolution=9)
    print(client.get(cell))
    print(client.query_disk(cell, k=1))
```

### Common patterns (summary)

```python
from h3lib import H3Client, IndexMode, open_client

# Client
client = open_client("sqlite", cache=True, index_mode=IndexMode.H3_INDEX)

# Hierarchy / traversal / measures
parent = client.cell_to_parent(cell, 7)
ring = client.grid_ring(cell, 1)
print(client.cell_area(cell), "km^2")

# Modes: cell / directed edge / vertex / topology
cell = client.put_cell((37.77, -122.42), {"n": 1}, resolution=9)
edge = client.put_directed_edge(cell, destination=client.grid_disk(cell, 1)[1])
vertex = client.put_vertex(cell=cell, vertex_num=0, payload={"corner": 0})
topo = client.put_topology((37.77, -122.42), {"place": "SF"}, resolution=9)

# Analytics
agg = client.aggregate_points([(37.77, -122.42), (37.7701, -122.4201)], resolution=8)
smoothed = client.smooth_disk({c: v["weight"] for c, v in agg.items()}, k=1)

# DuckDB + native disk
client = open_client("duckdb", enable_h3=True, prefer_db=True, cache=True)

# Redis cache
client = open_client(
    "sqlite",
    cache=True,
    redis_url="redis://127.0.0.1:6379/0",
    cache_options={"prefix": "h3lib:"},
)

# Postgres + PostGIS + h3-pg
pg = H3Client.from_config(
    store="postgres",
    store_options={
        "dsn": "postgresql://h3lib:h3lib@127.0.0.1:5432/h3lib",
        "enable_postgis": True,
        "enable_h3": True,
        "enable_h3_postgis": True,
        "require_postgis": True,
        "require_h3": True,
    },
    prefer_db=True,
)
```

See the full walkthroughs on the docs site:

- [Installation](https://vickykumar7125.github.io/h3lib/installation/)
- [Quickstart](https://vickykumar7125.github.io/h3lib/quickstart/)
- [Client & configuration](https://vickykumar7125.github.io/h3lib/client/)
- [Indexing & modes](https://vickykumar7125.github.io/h3lib/indexing/)
- [CRUD](https://vickykumar7125.github.io/h3lib/crud/)
- [Hierarchy](https://vickykumar7125.github.io/h3lib/hierarchy/) · [Traversal](https://vickykumar7125.github.io/h3lib/traversal/) · [Measures](https://vickykumar7125.github.io/h3lib/measures/)
- [Queries](https://vickykumar7125.github.io/h3lib/queries/) · [Analytics](https://vickykumar7125.github.io/h3lib/analytics/)
- [Stores](https://vickykumar7125.github.io/h3lib/stores/) · [Cache](https://vickykumar7125.github.io/h3lib/cache/) · [Docker](https://vickykumar7125.github.io/h3lib/docker/)
- [API overview](https://vickykumar7125.github.io/h3lib/api/)

---

## Database backends

| Backend | Native H3 / spatial | Notes |
|---------|---------------------|-------|
| **DuckDB** | Community `h3` | `INSTALL h3 FROM community; LOAD h3;` |
| **PostgreSQL** | PostGIS + h3-pg | `CREATE EXTENSION` postgis / h3 / h3_postgis |
| **SQLite** | Python H3 UDFs | Default local store |
| **MySQL** | Optional `POINT` centroid | H3 in Python |
| **MongoDB** | Unique `cell` + optional `2dsphere` | H3 in Python |

`query_disk` returns **stored** neighbors only. With `prefer_db=True` and native H3, the disk expands inside the database.

---

## Docker backends

```bash
docker compose up -d --build
pip install -e ".[all]"
pytest -q -m integration
```

| Service | Connect |
|---------|---------|
| Postgres (PostGIS + h3-pg) | `postgresql://h3lib:h3lib@127.0.0.1:5432/h3lib` |
| MySQL | `h3lib`/`h3lib` @ `127.0.0.1:3306` |
| MongoDB Atlas Local | `mongodb://127.0.0.1:27017/?directConnection=true` |
| Redis Stack | `redis://127.0.0.1:6379/0` (Insight `:8001`) |

---

## Package layout

```text
src/h3lib/     # client, ops, hierarchy, traversal, measures, analytics, store/, cache/
docs/          # MkDocs Material site → GitHub Pages
examples/
tests/
docker/postgres/
```

---

## Tests & CI

```bash
pip install -e ".[dev]"
pytest -q
pytest -q -m "not integration"
pytest -q -m integration
ruff check src tests
```

---

## Documentation & links

| Resource | URL |
|----------|-----|
| **Docs website** | https://vickykumar7125.github.io/h3lib/ |
| GitHub | https://github.com/vickykumar7125/h3lib |
| Issues | https://github.com/vickykumar7125/h3lib/issues |
| Releases | https://github.com/vickykumar7125/h3lib/releases |
| Uber H3 docs | https://h3geo.org/docs/ |
| h3-py | https://github.com/uber/h3-py |
| h3-pg | https://github.com/postgis/h3-pg |

---

## License

MIT — see [LICENSE](LICENSE).
