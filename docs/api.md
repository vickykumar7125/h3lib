# API overview

Public exports from `import h3lib`:

## Client

- `H3Client`, `open_client`

## Index modes

- `IndexMode`, `IndexInfo`
- `detect_mode`, `describe_index`, `get_index_resolution`
- `index_from_latlng`, `mode_metadata`, `related_indexes`

## H3 ops / hierarchy / traversal / measures

- `latlng_to_cell`, `cell_to_latlng`, `grid_disk`, `polygon_to_cells`
- `cell_to_parent`, `cell_to_children`, `cell_to_center_child`, `compact_cells`, `uncompact_cells`
- `grid_ring`, `grid_disk_distances`, `grid_distance`, `grid_path_cells`
- `cell_to_local_ij`, `local_ij_to_cell`
- `cell_area`, `average_hexagon_area`, `average_hexagon_edge_length`, `edge_length`
- `get_num_cells`, `get_res0_cells`, `get_pentagons`, `cells_to_geo`

## Analytics

- `aggregate_points`, `smooth_disk`

## Stores & cache

- `create_store`, `SQLiteStore`, `DuckDBStore`, `PostgresStore`, `MySQLStore`, `MongoStore`
- `create_cache`, `InMemoryCache`, `RedisCache`
- `ExtensionStatus`

## Exceptions

- `H3LibError`, `MissingDependencyError`, `StoreError`, `CacheError`
- `ConfigurationError`, `ExtensionError`, `IndexError_`

Optional backends (`PostgresStore`, `MySQLStore`, `MongoStore`, `RedisCache`) load lazily on first access.

Version: `h3lib.__version__` → `0.1.0`
