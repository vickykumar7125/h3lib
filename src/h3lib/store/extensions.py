"""Database extension detection, install, and actionable guidance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from h3lib.exceptions import ExtensionError


@dataclass
class ExtensionStatus:
    """Result of enabling / probing backend extensions."""

    backend: str
    enabled: dict[str, bool] = field(default_factory=dict)
    messages: list[str] = field(default_factory=list)
    available_native_h3: bool = False

    def require(self, name: str) -> None:
        if not self.enabled.get(name):
            hint = "\n".join(self.messages) or f"Extension '{name}' is not available."
            raise ExtensionError(hint)


# ---------------------------------------------------------------------------
# DuckDB
# ---------------------------------------------------------------------------

def enable_duckdb_extensions(
    conn: Any,
    *,
    enable_h3: bool = True,
    enable_spatial: bool = False,
    require_h3: bool = False,
) -> ExtensionStatus:
    """
    Install/load DuckDB community H3 (and optionally spatial).

    Uses: INSTALL h3 FROM community; LOAD h3;
    """
    status = ExtensionStatus(backend="duckdb")

    if enable_h3:
        err = _duckdb_install_load(conn, "h3", from_community=True)
        if err is None:
            status.enabled["h3"] = True
            status.available_native_h3 = True
            status.messages.append("DuckDB H3 extension installed/loaded.")
        else:
            status.enabled["h3"] = False
            status.messages.append(
                "DuckDB H3 extension could not be enabled.\n"
                "Try manually in a DuckDB session:\n"
                "  INSTALL h3 FROM community;\n"
                "  LOAD h3;\n"
                f"Underlying error: {err}"
            )
            if require_h3:
                status.require("h3")
    else:
        status.enabled["h3"] = False

    if enable_spatial:
        err = _duckdb_install_load(conn, "spatial", from_community=False)
        if err is None:
            status.enabled["spatial"] = True
            status.messages.append("DuckDB spatial extension installed/loaded.")
        else:
            status.enabled["spatial"] = False
            status.messages.append(
                "DuckDB spatial extension could not be enabled.\n"
                "Try: INSTALL spatial; LOAD spatial;\n"
                f"Underlying error: {err}"
            )

    return status


def _duckdb_install_load(conn: Any, name: str, *, from_community: bool) -> str | None:
    attempts = []
    if from_community:
        attempts.append(f"INSTALL {name} FROM community; LOAD {name};")
    attempts.extend(
        [
            f"INSTALL {name}; LOAD {name};",
            f"LOAD {name};",
        ]
    )
    last_err: Exception | None = None
    for sql in attempts:
        try:
            conn.execute(sql)
            return None
        except Exception as exc:  # noqa: BLE001 - collect best error for user
            last_err = exc
    return str(last_err) if last_err else "unknown error"


# ---------------------------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------------------------

def enable_postgres_extensions(
    conn: Any,
    *,
    enable_postgis: bool = True,
    enable_h3: bool = True,
    enable_h3_postgis: bool = True,
    require_postgis: bool = False,
    require_h3: bool = False,
) -> ExtensionStatus:
    """
    Ensure PostGIS / h3 / h3_postgis are available in the connected database.

    CREATE EXTENSION is attempted when missing. If the OS package is not
    installed, raise/report clear install instructions for the user.
    """
    status = ExtensionStatus(backend="postgres")

    if enable_postgis:
        ok, msg = _pg_ensure_extension(
            conn,
            "postgis",
            install_hint=(
                "PostGIS is not installed on this PostgreSQL server.\n"
                "Install the PostGIS package for your Postgres version, then retry.\n"
                "  Debian/Ubuntu: sudo apt install postgresql-<ver>-postgis-3\n"
                "  Windows: use Stack Builder / PostGIS Bundle\n"
                "Then run: CREATE EXTENSION postgis;"
            ),
        )
        status.enabled["postgis"] = ok
        status.messages.append(msg)
        if require_postgis and not ok:
            raise ExtensionError(msg)

    if enable_h3:
        ok, msg = _pg_ensure_extension(
            conn,
            "h3",
            install_hint=(
                "PostgreSQL H3 extension (h3-pg) is not installed on this server.\n"
                "Install it, then retry:\n"
                "  Debian/Ubuntu: sudo apt install postgresql-<ver>-h3\n"
                "  RHEL: sudo yum install h3-pg_<ver>\n"
                "  Windows: PostGIS Bundle extras include h3\n"
                "  Or: pgxn install h3\n"
                "Then run: CREATE EXTENSION h3;"
            ),
        )
        status.enabled["h3"] = ok
        status.available_native_h3 = ok
        status.messages.append(msg)
        if require_h3 and not ok:
            raise ExtensionError(msg)

    if enable_h3_postgis and status.enabled.get("h3"):
        ok, msg = _pg_ensure_extension(
            conn,
            "h3_postgis",
            cascade=True,
            install_hint=(
                "Could not enable h3_postgis (needs postgis + h3 packages).\n"
                "Ensure PostGIS and h3-pg are installed, then:\n"
                "  CREATE EXTENSION postgis;\n"
                "  CREATE EXTENSION h3;\n"
                "  CREATE EXTENSION h3_postgis CASCADE;"
            ),
        )
        status.enabled["h3_postgis"] = ok
        status.messages.append(msg)
    elif enable_h3_postgis:
        status.enabled["h3_postgis"] = False
        status.messages.append(
            "Skipped h3_postgis because core h3 extension is not available."
        )

    return status


def _pg_extension_exists(conn: Any, name: str) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM pg_extension WHERE extname = %s",
        (name,),
    )
    return cur.fetchone() is not None


def _pg_ensure_extension(
    conn: Any,
    name: str,
    *,
    cascade: bool = False,
    install_hint: str,
) -> tuple[bool, str]:
    if _pg_extension_exists(conn, name):
        return True, f"PostgreSQL extension '{name}' is already enabled."

    sql = f"CREATE EXTENSION IF NOT EXISTS {name}"
    if cascade:
        sql += " CASCADE"
    try:
        conn.execute(sql)
        conn.commit()
        if _pg_extension_exists(conn, name):
            return True, f"PostgreSQL extension '{name}' was created successfully."
        return (
            False,
            f"CREATE EXTENSION {name} reported success but extension is missing.\n"
            f"{install_hint}",
        )
    except Exception as exc:
        try:
            conn.rollback()
        except Exception:
            pass
        return (
            False,
            f"Failed to CREATE EXTENSION {name}.\n{install_hint}\nUnderlying error: {exc}",
        )


# ---------------------------------------------------------------------------
# MySQL / SQLite / Mongo guidance + lightweight substitutes
# ---------------------------------------------------------------------------

MYSQL_EXTENSION_NOTES = (
    "MySQL has no official H3 or PostGIS-equivalent extension. "
    "h3lib creates an InnoDB table with a PRIMARY KEY on `cell` and optional "
    "POINT + SPATIAL INDEX columns for centroid-based lookups. "
    "H3 cell math still runs in Python via the h3 package."
)

SQLITE_EXTENSION_NOTES = (
    "SQLite has no official H3 extension. "
    "h3lib registers Python H3 UDFs (h3_latlng_to_cell, h3_cell_to_latlng, "
    "h3_grid_disk) on the connection and keeps a PRIMARY KEY on `cell`. "
    "Optional SpatiaLite is not required."
)

MONGO_EXTENSION_NOTES = (
    "MongoDB has no H3 server extension. "
    "h3lib ensures a unique index on `cell` and an optional 2dsphere index on "
    "`location` for centroid queries. H3 cell math runs in Python."
)


def mysql_extension_status(*, spatial_index: bool) -> ExtensionStatus:
    status = ExtensionStatus(backend="mysql", available_native_h3=False)
    status.enabled["native_h3"] = False
    status.enabled["spatial_index"] = spatial_index
    status.messages.append(MYSQL_EXTENSION_NOTES)
    if spatial_index:
        status.messages.append("Created optional POINT column + SPATIAL INDEX when supported.")
    return status


def sqlite_extension_status(*, udfs_registered: bool) -> ExtensionStatus:
    status = ExtensionStatus(backend="sqlite", available_native_h3=False)
    status.enabled["native_h3"] = False
    status.enabled["python_h3_udfs"] = udfs_registered
    status.messages.append(SQLITE_EXTENSION_NOTES)
    if udfs_registered:
        status.messages.append("Registered Python H3 UDFs on this SQLite connection.")
    return status


def mongo_extension_status(*, cell_index: bool, geo_index: bool) -> ExtensionStatus:
    status = ExtensionStatus(backend="mongo", available_native_h3=False)
    status.enabled["native_h3"] = False
    status.enabled["cell_index"] = cell_index
    status.enabled["geo_2dsphere"] = geo_index
    status.messages.append(MONGO_EXTENSION_NOTES)
    return status
