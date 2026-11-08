"""
PostgreSQL PostGIS + h3-pg bootstrap example.

Requires a running Postgres and:
  pip install -e ".[postgres]"

If OS packages are missing, extension_status.messages / ExtensionError
explain how to install them.
"""

from h3lib import ExtensionError, open_client


DSN = "postgresql://postgres:postgres@localhost:5432/h3lib"


def main() -> None:
    try:
        client = open_client(
            "postgres",
            dsn=DSN,
            enable_postgis=True,
            enable_h3=True,
            enable_h3_postgis=True,
            require_postgis=False,
            require_h3=False,
            prefer_db=True,
        )
    except ExtensionError as exc:
        print("Required extension missing:\n", exc)
        return
    except Exception as exc:
        print("Could not connect to Postgres:\n", exc)
        print("Update DSN in examples/postgres_extensions.py and retry.")
        return

    status = client.extension_status
    print("enabled:", status.enabled if status else None)
    if status:
        for msg in status.messages:
            print("-", msg)

    cell = client.put((37.7749, -122.4194), {"name": "SF"}, resolution=9)
    print("stored:", cell, client.get(cell))
    if client.supports_native_h3:
        for n in client.grid_disk(cell, 1):
            client.put(n, {"neighbor": True})
        print("native disk hits:", len(client.query_disk(cell, 1)))
    client.close()


if __name__ == "__main__":
    main()
