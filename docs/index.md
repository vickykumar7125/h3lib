# h3lib

**h3lib** is a Python geospatial indexing SDK built on [Uber H3](https://h3geo.org/) (via [h3-py](https://github.com/uber/h3-py)).  
It adds pluggable storage backends, optional caching, index modes, analytics helpers, and native DB H3 where available.

| | |
|---|---|
| **Documentation** | [https://vickykumar7125.github.io/h3lib/](https://vickykumar7125.github.io/h3lib/) |
| **Source** | [github.com/vickykumar7125/h3lib](https://github.com/vickykumar7125/h3lib) |
| **Releases** | [Releases](https://github.com/vickykumar7125/h3lib/releases) |
| **Requires** | Python ≥ 3.10 |

## Why h3lib?

| Capability | What you get |
|---|---|
| H3 surface | Indexing, hierarchy, traversal, measures, GeoJSON |
| Index modes | `h3_index`, `cell`, `directed_edge`, `vertex` |
| Persistence | SQLite, DuckDB, Postgres (+ PostGIS/h3-pg), MySQL, MongoDB |
| Cache | Redis or in-memory |
| Analytics | Point→hex aggregation and k-ring smoothing |
| Queries | Disk / polygon / edge / vertex lookups over stored data |

## 60-second start

```bash
pip install https://github.com/vickykumar7125/h3lib/releases/download/v0.1.0/h3lib-0.1.0-py3-none-any.whl
```

```python
from h3lib import open_client

with open_client("sqlite") as client:
    cell = client.put((37.7749, -122.4194), {"name": "SF"}, resolution=9)
    print(client.get(cell))
    print(client.query_disk(cell, k=1))
```

## Next steps

1. [Installation](installation.md) — conda, extras, wheel from GitHub Releases  
2. [Quickstart](quickstart.md) — common workflows  
3. [Stores](stores.md) — choose SQLite, DuckDB, Postgres, MySQL, or Mongo  
4. [API overview](api.md) — public exports  

!!! tip "Official H3 docs"
    Geometry and algorithm details live in the [H3 documentation](https://h3geo.org/docs/). h3lib wraps h3-py and focuses on storage, modes, and app-level workflows.
