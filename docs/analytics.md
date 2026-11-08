# Analytics

Dataframe-agnostic helpers (no pandas required).

## aggregate_points

Bin lat/lng points into H3 cells:

```python
from h3lib import open_client

points = [
    (37.7749, -122.4194),
    (37.7750, -122.4195, 2.0),                 # optional weight as 3rd value
    {"lat": 37.7748, "lng": -122.4193, "w": 3},
]

with open_client("sqlite") as client:
    agg = client.aggregate_points(points, resolution=8, weight_key="w")
    # {cell: {"count": N, "weight": W}, ...}
```

Missing `lat`/`lng` keys raise `ValueError` with a clear message.

## smooth_disk

Neighborhood average over each cell’s grid disk (stored-subset: only neighbors present in `values`):

```python
values = {c: v["weight"] for c, v in agg.items()}
smoothed = client.smooth_disk(values, k=1, value_key="weight", include_center=True)
```

`k` must be `>= 0`.
