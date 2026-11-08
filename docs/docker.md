# Docker backends

Local integration stack for Postgres (PostGIS + h3-pg), MySQL, MongoDB Atlas Local, and Redis Stack.

```bash
docker compose up -d --build
pip install -e ".[all]"
pytest -q -m integration
docker compose down
```

| Service | Image | Connect |
|---------|-------|---------|
| Postgres | `h3lib-postgis-h3:16` | `postgresql://h3lib:h3lib@127.0.0.1:5432/h3lib` |
| MySQL | `mysql:8.4` | `h3lib` / `h3lib` @ `127.0.0.1:3306` / db `h3lib` |
| MongoDB | `mongodb/mongodb-atlas-local` | `mongodb://127.0.0.1:27017/?directConnection=true` |
| Redis Stack | `redis/redis-stack` | `redis://127.0.0.1:6379/0` (no password); Insight `:8001` |

Ports bind to **127.0.0.1** only.

Postgres image is built from [`docker/postgres/Dockerfile`](https://github.com/vickykumar7125/h3lib/blob/main/docker/postgres/Dockerfile) (`postgres:16-bookworm` + PostGIS + **h3-pg**).
