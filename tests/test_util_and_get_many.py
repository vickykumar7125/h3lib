"""Payload decoding and get_many strict mode."""

import pytest

from h3lib import IndexError_, StoreError, open_client
from h3lib._util import loads_payload


def test_loads_payload_corrupt_json():
    with pytest.raises(StoreError):
        loads_payload("{not-json")


def test_get_many_strict_raises():
    with open_client("sqlite") as client:
        cell = client.put((37.77, -122.42), {"ok": 1}, resolution=9)
        with pytest.raises(IndexError_):
            client.get_many([cell, "not-an-h3-index"], strict=True)
        # default silently filters invalid
        assert cell in client.get_many([cell, "not-an-h3-index"])
