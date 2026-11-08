"""MongoDB store backend (optional) — indexes instead of H3 server extension."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from h3lib._util import require_module
from h3lib.exceptions import StoreError
from h3lib.store.base import Store
from h3lib.store.extensions import ExtensionStatus, mongo_extension_status


class MongoStore(Store):
    def __init__(
        self,
        uri: str = "mongodb://localhost:27017",
        *,
        database: str = "h3lib",
        collection: str = "h3_cells",
        client: Any | None = None,
        enable_geo_index: bool = True,
    ) -> None:
        pymongo = require_module("pymongo", "mongo")
        self._client = client or pymongo.MongoClient(uri)
        self._owns_client = client is None
        try:
            self._col = self._client[database][collection]
            self._col.create_index("cell", unique=True)
            cell_ok = True
        except Exception as exc:
            if self._owns_client:
                try:
                    self._client.close()
                except Exception:
                    pass
            raise StoreError(
                "Failed to create unique index on MongoDB 'cell' field; "
                "duplicate cells may be stored without it"
            ) from exc

        geo_ok = False
        if enable_geo_index:
            try:
                # GeoJSON Point field for optional centroid queries.
                self._col.create_index([("location", "2dsphere")])
                geo_ok = True
            except Exception:
                geo_ok = False

        self.extension_status: ExtensionStatus = mongo_extension_status(
            cell_index=cell_ok,
            geo_index=geo_ok,
        )
        self.h3_extension_loaded = False

    def _location_from_payload(
        self, payload: Mapping[str, Any] | None
    ) -> dict[str, Any] | None:
        data = dict(payload or {})
        if "location" in data and isinstance(data["location"], dict):
            return data["location"]
        # Prefer stamped H3 coords when present.
        lat = data.get("_h3_lat", data.get("lat"))
        lng = data.get("_h3_lng", data.get("lng"))
        if lat is None or lng is None:
            return None
        try:
            return {
                "type": "Point",
                "coordinates": [float(lng), float(lat)],
            }
        except (TypeError, ValueError):
            return None

    def put(self, cell: str, payload: Mapping[str, Any] | None = None) -> None:
        doc: dict[str, Any] = {
            "cell": cell,
            "payload": dict(payload or {}),
        }
        location = self._location_from_payload(payload)
        update: dict[str, Any] = {"$set": doc}
        if location is not None:
            doc["location"] = location
        else:
            update["$unset"] = {"location": ""}
        self._col.update_one({"cell": cell}, update, upsert=True)

    def get(self, cell: str) -> dict[str, Any] | None:
        doc = self._col.find_one({"cell": cell}, {"_id": 0, "payload": 1})
        if doc is None:
            return None
        payload = doc.get("payload")
        return dict(payload) if isinstance(payload, dict) else {"value": payload}

    def delete(self, cell: str) -> bool:
        result = self._col.delete_one({"cell": cell})
        return result.deleted_count > 0

    def get_many(self, cells: Iterable[str]) -> dict[str, dict[str, Any]]:
        cell_list = list(cells)
        if not cell_list:
            return {}
        out: dict[str, dict[str, Any]] = {}
        for doc in self._col.find({"cell": {"$in": cell_list}}, {"_id": 0}):
            cell = doc.get("cell")
            payload = doc.get("payload")
            if cell is None:
                continue
            out[str(cell)] = dict(payload) if isinstance(payload, dict) else {"value": payload}
        return out

    def put_many(self, items: Mapping[str, Mapping[str, Any] | None]) -> None:
        if not items:
            return
        pymongo = require_module("pymongo", "mongo")
        ops = []
        for cell, payload in items.items():
            data = dict(payload or {})
            doc: dict[str, Any] = {"cell": cell, "payload": data}
            location = self._location_from_payload(data)
            update: dict[str, Any] = {"$set": doc}
            if location is not None:
                doc["location"] = location
            else:
                update["$unset"] = {"location": ""}
            ops.append(pymongo.UpdateOne({"cell": cell}, update, upsert=True))
        self._col.bulk_write(ops, ordered=False)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
