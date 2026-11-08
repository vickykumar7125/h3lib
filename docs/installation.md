# Installation

## Requirements

- Python **3.10+** (tested through 3.14)
- Core deps: `h3`, `duckdb`

## Install from GitHub Release (recommended)

```bash
pip install https://github.com/vickykumar7125/h3lib/releases/download/v0.1.0/h3lib-0.1.0-py3-none-any.whl
```

Or the source archive:

```bash
pip install https://github.com/vickykumar7125/h3lib/releases/download/v0.1.0/h3lib-0.1.0.tar.gz
```

## Install from source (editable)

```bash
git clone https://github.com/vickykumar7125/h3lib.git
cd h3lib
conda create -n h3-lib python=3.11 -y
conda activate h3-lib
pip install -e .
```

### Optional extras

| Extra | Packages | Purpose |
|-------|----------|---------|
| `redis` | `redis` | Redis cache backend |
| `postgres` | `psycopg[binary]` | PostgreSQL + PostGIS / h3-pg |
| `mysql` | `pymysql` | MySQL store |
| `mongo` | `pymongo` | MongoDB store |
| `dev` | `pytest`, `ruff`, `mypy` | Tests & lint |
| `all` | everything above | Full local setup |

```bash
pip install -e ".[redis]"
pip install -e ".[postgres]"
pip install -e ".[mysql]"
pip install -e ".[mongo]"
pip install -e ".[dev]"
pip install -e ".[all]"
```

## Install from git tip

```bash
pip install "git+https://github.com/vickykumar7125/h3lib.git@main"
pip install "git+https://github.com/vickykumar7125/h3lib.git@v0.1.0"
```

## Verify

```python
import h3lib
print(h3lib.__version__)

from h3lib import open_client
with open_client("sqlite") as c:
    print(c.latlng_to_cell(0, 0, 5))
```

## Docs site (local)

```bash
pip install -r requirements-docs.txt
mkdocs serve
# open http://127.0.0.1:8000
```
