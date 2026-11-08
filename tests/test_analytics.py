"""Analytics helpers: aggregate_points and smooth_disk."""

from h3lib import aggregate_points, latlng_to_cell, open_client, smooth_disk


def test_aggregate_points_same_cell():
    # Three nearby SF points that share a coarse cell.
    points = [
        (37.7749, -122.4194),
        (37.7750, -122.4195),
        (37.7748, -122.4193),
    ]
    res = 7
    agg = aggregate_points(points, res)
    cells = {latlng_to_cell(lat, lng, res) for lat, lng in points}
    assert set(agg) == cells
    total_count = sum(v["count"] for v in agg.values())
    assert total_count == 3


def test_aggregate_points_mapping_and_weight():
    points = [
        {"lat": 37.77, "lng": -122.42, "w": 2},
        {"lat": 37.77, "lng": -122.42, "w": 3},
    ]
    agg = aggregate_points(points, 8, weight_key="w")
    assert len(agg) == 1
    only = next(iter(agg.values()))
    assert only["count"] == 2
    assert only["weight"] == 5


def test_smooth_disk_averages_neighbors():
    cell = latlng_to_cell(37.7749, -122.4194, 9)
    with open_client("sqlite") as client:
        neighbors = client.grid_disk(cell, 1)
    values = {c: 0.0 for c in neighbors}
    values[cell] = 10.0
    # Put a known value on one neighbor
    ring = [c for c in neighbors if c != cell]
    values[ring[0]] = 2.0
    smoothed = smooth_disk(values, k=1)
    assert cell in smoothed
    # Center average includes 10 + 2 + zeros over all disk members present
    assert smoothed[cell] == sum(values.values()) / len(values)


def test_client_aggregate_and_smooth():
    with open_client("sqlite") as client:
        agg = client.aggregate_points([(37.77, -122.42), (37.7701, -122.4201)], resolution=8)
        assert agg
        smoothed = client.smooth_disk({c: v["weight"] for c, v in agg.items()}, k=1)
        assert smoothed
