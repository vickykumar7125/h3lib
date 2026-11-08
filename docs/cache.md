# Cache

## Policy

| Situation | Result |
|-----------|--------|
| `cache=False` / `enabled=False` | No cache (`None`) |
| `cache=True` + Redis URL/client | `RedisCache` |
| `cache=True` without Redis | `InMemoryCache` |
| Explicit `backend="memory"` | Memory even if `redis_url` is set |

```python
from h3lib import create_cache, open_client

# Memory
client = open_client("sqlite", cache=True)

# Redis — prefix must be non-empty
client = open_client(
    "sqlite",
    cache=True,
    redis_url="redis://127.0.0.1:6379/0",
    cache_options={"prefix": "h3lib:"},
)

cache = create_cache(enabled=True, backend="memory")
cache = create_cache(enabled=False, backend="redis")  # → None
```

## Operations

```python
cache.set("cell", {"x": 1}, ttl=60)
cache.get("cell")
cache.set_many({"a": {"v": 1}, "b": {"v": 2}})
cache.get_many(["a", "b"])
cache.delete("a")
cache.clear()   # Redis: SCAN+DELETE under prefix only
cache.close()   # does not close an injected Redis client
```

In-memory cache is lock-protected for basic thread safety.
