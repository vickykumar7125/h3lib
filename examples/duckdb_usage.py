"""DuckDB store with H3 community extension + native disk query."""

from h3lib import create_store, open_client


def main() -> None:
    with open_client(
        "duckdb",
        path=":memory:",
        cache=True,
        enable_h3=True,
        require_h3=False,
        prefer_db=True,
    ) as client:
        cell = client.put((40.7128, -74.0060), {"name": "NYC"}, resolution=8)
        print("duckdb cell:", cell, client.get(cell))
        status = client.extension_status
        print("extensions:", status.enabled if status else None)
        print("supports_native_h3:", client.supports_native_h3)

        if client.supports_native_h3:
            for n in client.grid_disk(cell, 1):
                client.put(n, {"neighbor": True})
            hits = client.query_disk(cell, 1)
            print("native disk hits:", len(hits))

    store = create_store("duckdb", path=":memory:", enable_h3=True)
    if store.h3_extension_loaded:
        rows = store.query_cells_sql(
            "SELECT h3_h3_to_string(h3_latlng_to_cell(37.7749, -122.4194, 9))"
        )
        print("duckdb h3 sql:", rows)
    else:
        print("H3 extension not loaded; messages:")
        for msg in store.extension_status.messages:
            print("-", msg)
    store.close()


if __name__ == "__main__":
    main()
