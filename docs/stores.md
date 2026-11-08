# Stores

Create via `open_client`, `H3Client.from_config`, or `create_store`.

## Comparison

| Backend | Extra | Native H3 | Notes |
|---------|-------|-----------|-------|
| SQLite | core | Python UDFs | Default; great for local/dev |
| DuckDB | core | Community `h3` | Fast analytical + in-DB disk |
| Postgres | `postgres` | PostGIS + **h3-pg** | Production geo + native disk |
| MySQL | `mysql` | — | Optional centroid POINT |
| MongoDB | `mongo` | — | Unique `cell` + optional 2dsphere |

## SQLite

```python
client = open_client("sqlite", path="h3.db", register_h3_udfs=True)
```

## DuckDB

```python
client = open_client(
    "duckdb",
    path="h3.duckdb",
    enable_h3=True,
    require_h3=False,
    prefer_db=True,
)
print(client.supports_native_h3)
print(client.store.extension_status.enabled)
```

## PostgreSQL (PostGIS + h3-pg)

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
```

When PostGIS is on, `geom` is populated from stamped lat/lng on `put`.

## MySQL

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

## MongoDB

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

## Extension errors

```python
from h3lib import ExtensionError, create_store

try:
    create_store("duckdb", enable_h3=True, require_h3=True)
except ExtensionError as e:
    print(e)  # actionable install guidance
```

SQL `table` names must match `^[A-Za-z_][A-Za-z0-9_]*$` or `schema.table`.
