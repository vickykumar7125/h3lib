"""Internal helpers."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

from h3lib.exceptions import ConfigurationError, MissingDependencyError, StoreError

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def require_module(module_name: str, extra: str):
    try:
        return __import__(module_name)
    except ImportError as exc:
        raise MissingDependencyError(
            f"Optional dependency '{module_name}' is required for this backend. "
            f"Install with: pip install h3lib[{extra}]"
        ) from exc


def dumps_payload(payload: Mapping[str, Any] | None) -> str:
    return json.dumps(payload if payload is not None else {}, default=str)


def loads_payload(raw: str | bytes | None) -> dict[str, Any] | None:
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StoreError(f"Corrupt JSON payload: {exc}") from exc
    if data is None:
        return None
    if not isinstance(data, dict):
        return {"value": data}
    return data


def validate_sql_identifier(
    name: str,
    *,
    allow_schema: bool = True,
    kind: str = "table",
) -> str:
    """
    Validate a SQL identifier (table or schema.table).

    Returns the original name after validation (caller quotes for the dialect).
    """
    raw = str(name).strip()
    if not raw:
        raise ConfigurationError(f"Empty SQL {kind} name is not allowed")
    parts = raw.split(".")
    if len(parts) == 1:
        candidates = parts
    elif allow_schema and len(parts) == 2:
        candidates = parts
    else:
        raise ConfigurationError(
            f"Invalid SQL {kind} name {name!r}. "
            "Use an unquoted identifier matching [A-Za-z_][A-Za-z0-9_]* "
            "or schema.table"
        )
    for part in candidates:
        if not _IDENT_RE.fullmatch(part):
            raise ConfigurationError(
                f"Invalid SQL {kind} identifier {name!r}. "
                "Only letters, digits, and underscore are allowed "
                "(must start with a letter or underscore)."
            )
    return raw


def quote_ident_pg(name: str) -> str:
    """Quote a validated Postgres identifier (supports schema.table)."""
    return ".".join(f'"{part}"' for part in name.split("."))


def quote_ident_mysql(name: str) -> str:
    """Quote a validated MySQL identifier (supports database.table)."""
    return ".".join(f"`{part}`" for part in name.split("."))
