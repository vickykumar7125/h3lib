# Client & configuration

## Constructors

### `open_client` (recommended)

```python
from h3lib import IndexMode, open_client

client = open_client(
    "sqlite",                 # store backend name
    path=":memory:",          # store-specific kwargs are forwarded
    cache=True,               # enable cache
    redis_url=None,           # if set → Redis, else memory when cache=True
    prefer_db=True,           # use native H3 disk queries when available
    index_mode=IndexMode.H3_INDEX,
    stamp_mode_metadata=True,
    default_resolution=9,
    cache_ttl=None,
)
```

Unknown keyword arguments raise `ConfigurationError`.

### `H3Client.from_config`

```python
from h3lib import H3Client

client = H3Client.from_config(
    store="duckdb",
    store_options={"path": ":memory:", "enable_h3": True},
    cache_enabled=True,
    redis_url=None,
    cache_backend=None,
    cache_options={},
    default_resolution=9,
    prefer_db=True,
    index_mode="h3_index",
    stamp_mode_metadata=True,
)
```

### Explicit wiring

```python
from h3lib import H3Client, create_cache, create_store

store = create_store("sqlite", path="h3.db")
cache = create_cache(enabled=True)  # InMemoryCache
client = H3Client(store=store, cache=cache)
```

## Lifecycle

```python
client = open_client("sqlite")
try:
    ...
finally:
    client.close()

# or
with open_client("sqlite") as client:
    ...
```

`close()` closes the store and cache (owned Redis connections only).

## Important flags

| Flag | Default | Meaning |
|------|---------|---------|
| `prefer_db` | `True` | Prefer native DB `query_disk` when `supports_native_h3` |
| `stamp_mode_metadata` | `True` | Stamp `_h3_*` fields on put |
| `index_mode` | `h3_index` | Accepted index kinds |
| `default_resolution` | `9` | Used when putting from lat/lng without resolution |
| `cache_ttl` | `None` | Seconds; `None` = no expiry |

## Properties

```python
client.supports_native_h3   # bool
client.extension_status     # ExtensionStatus | None (from store)
client.store
client.cache                # Cache | None
```
