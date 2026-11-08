"""Basic h3lib usage with SQLite + in-memory cache."""

from h3lib import open_client


def main() -> None:
    with open_client("sqlite", cache=True) as client:
        cell = client.put((37.7749, -122.4194), {"name": "San Francisco"}, resolution=9)
        print("stored:", cell)
        print("fetched:", client.get(cell))

        nearby = client.query_disk(cell, k=1)
        print("disk hits:", len(nearby))

        ring = [
            (37.78, -122.43),
            (37.78, -122.40),
            (37.76, -122.40),
            (37.76, -122.43),
        ]
        poly_hits = client.query_polygon(ring, resolution=9)
        print("polygon hits:", len(poly_hits))


if __name__ == "__main__":
    main()
