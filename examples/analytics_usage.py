"""Point-to-hex aggregation and k-ring smoothing without pandas."""

from h3lib import open_client


def main() -> None:
    points = [
        (37.7749, -122.4194),
        (37.7750, -122.4195),
        (37.7748, -122.4193),
        (37.7800, -122.4100),
    ]
    with open_client("sqlite") as client:
        agg = client.aggregate_points(points, resolution=8)
        print("aggregates:", {c: v["count"] for c, v in agg.items()})
        values = {c: v["weight"] for c, v in agg.items()}
        smoothed = client.smooth_disk(values, k=1)
        print("smoothed:", {c: round(v, 3) for c, v in smoothed.items()})


if __name__ == "__main__":
    main()
