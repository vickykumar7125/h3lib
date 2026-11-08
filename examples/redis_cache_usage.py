"""Redis cache example — falls back to in-memory if Redis is unreachable/unavailable."""

from h3lib import H3Client, create_cache, create_store


def main() -> None:
    store = create_store("sqlite", path=":memory:")
    try:
        cache = create_cache(enabled=True, redis_url="redis://localhost:6379/0")
        # Probe Redis early so we can fall back cleanly.
        if cache is not None:
            cache.set("__ping__", {"ok": True}, ttl=5)
            cache.delete("__ping__")
        print("using Redis cache")
    except Exception as exc:
        print(f"Redis unavailable ({exc}); using in-memory cache")
        cache = create_cache(enabled=True)

    with H3Client(store=store, cache=cache) as client:
        cell = client.put((51.5074, -0.1278), {"name": "London"}, resolution=9)
        print(cell, client.get(cell))


if __name__ == "__main__":
    main()
