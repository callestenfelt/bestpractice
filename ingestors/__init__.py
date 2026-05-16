"""Structured-source ingestion adapters.

Each adapter is a Python module exposing:

    SOURCE_NAME: str          — human label shown on /admin/sources
    FEED_URL: str             — primary fetch URL
    CACHE_FILENAME: str       — relative path under data/cache/ for snapshot
    fetch_candidates(conn, source_row, max_new) -> list[dict]

The returned dicts carry the fields needed to INSERT INTO sub_considerations:
slug, one_liner, body, source_name, source_url, source_title, source_date.

The runner (collect_structured.py) dispatches to adapters by name via
sources.config_json -> adapter. Adapters own URL diff/dedup against
prior snapshots; the runner only handles DB writes and per-source
bookkeeping.
"""
from __future__ import annotations

import importlib
from typing import Protocol


class Adapter(Protocol):
    SOURCE_NAME: str
    FEED_URL: str
    CACHE_FILENAME: str

    @staticmethod
    def fetch_candidates(conn, source_row, max_new: int | None = None) -> list[dict]:
        ...


def load_adapter(name: str):
    """Import ingestors.<name> and return the module. ValueError on missing."""
    try:
        return importlib.import_module(f"ingestors.{name}")
    except ModuleNotFoundError as exc:
        raise ValueError(f"unknown adapter: {name}") from exc
