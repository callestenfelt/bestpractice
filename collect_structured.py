"""bestpractice — structured-source ingestion runner.

Walks sources WHERE type='structured' AND status IN ('active','error').
For each source, looks up its adapter via config_json -> adapter, calls
adapter.fetch_candidates(), and writes the returned candidates as
pending sub_considerations attached to the ingest-inbox consideration.

Adapters live under ingestors/ (one module per source). The runner is
intentionally thin — diff logic, schema knowledge, and URL handling all
live in the adapter; the runner only handles DB writes and per-source
bookkeeping (last_collected, item_count, status='error' on failures).

Usage: python collect_structured.py [--limit N] [--source NAME]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Windows cp1252 console crashes on non-ASCII; force utf-8 like collect.py / score.py.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

load_dotenv()

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("BESTPRACTICE_DB", str(ROOT / "data" / "bestpractice.db")))

# Import after sys.path is implicit (CWD), the ingestors package lives next to this file.
sys.path.insert(0, str(ROOT))
from ingestors import load_adapter  # noqa: E402


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def get_inbox_id(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT id FROM considerations WHERE parent_type='page_type' AND parent_slug='site-wide' AND slug='ingest-inbox'"
    ).fetchone()
    if not row:
        print("ERROR: ingest-inbox missing. Run python init_db.py.", file=sys.stderr)
        sys.exit(2)
    return row[0]


def collect_one(conn: sqlite3.Connection, source: sqlite3.Row, inbox_id: int, max_new: int | None) -> tuple[int, str]:
    """Returns (inserted, status). status is 'ok'|'304'|'error'."""
    print(f"\n[{source['name']}] type={source['type']}")
    config = {}
    if source["config_json"]:
        try:
            config = json.loads(source["config_json"])
        except json.JSONDecodeError:
            print(f"  bad config_json: {source['config_json']!r}")
            return 0, "error"
    adapter_name = config.get("adapter")
    if not adapter_name:
        print(f"  no 'adapter' key in config_json")
        return 0, "error"
    try:
        adapter = load_adapter(adapter_name)
    except ValueError as exc:
        print(f"  {exc}")
        return 0, "error"

    try:
        candidates = adapter.fetch_candidates(conn, source, max_new=max_new)
    except Exception as exc:  # noqa: BLE001
        print(f"  fetch error: {exc!r}")
        conn.execute(
            "UPDATE sources SET status='error', last_fetched=? WHERE id=?",
            (now_iso(), source["id"]),
        )
        conn.commit()
        return 0, "error"

    if not candidates:
        print("  no new candidates")
        conn.execute(
            "UPDATE sources SET last_fetched=? WHERE id=?",
            (now_iso(), source["id"]),
        )
        conn.commit()
        return 0, "ok"

    print(f"  {len(candidates)} new candidates")
    now = now_iso()
    inserted = 0
    for c in candidates:
        try:
            conn.execute(
                """INSERT INTO sub_considerations
                       (consideration_id, slug, one_liner, body,
                        source_name, source_title, source_url, source_date,
                        status, display_order, created_at, last_updated)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', 0, ?, ?)""",
                (inbox_id, c["slug"], c["one_liner"], c["body"],
                 c["source_name"], c["source_title"], c["source_url"], c["source_date"],
                 now, now),
            )
            inserted += 1
        except sqlite3.IntegrityError as exc:
            print(f"  dup or constraint: {exc}")

    conn.execute(
        """UPDATE sources
              SET status='active', last_collected=?, last_fetched=?,
                  item_count = item_count + ?
            WHERE id = ?""",
        (now, now, inserted, source["id"]),
    )
    conn.commit()
    print(f"  inserted {inserted}")
    return inserted, "ok"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Cap new candidates per source this run")
    parser.add_argument("--source", default=None, help="Only run the named source")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"ERROR: DB missing at {DB_PATH}. Run python init_db.py.", file=sys.stderr)
        return 2

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    inbox_id = get_inbox_id(conn)
    sql = "SELECT * FROM sources WHERE type='structured' AND status IN ('active','error')"
    params: tuple = ()
    if args.source:
        sql += " AND name=?"
        params = (args.source,)
    sql += " ORDER BY name"
    sources = conn.execute(sql, params).fetchall()

    print(f"db: {DB_PATH}")
    print(f"inbox: {inbox_id}")
    print(f"sources to fetch: {len(sources)}")
    if args.limit:
        print(f"per-source cap: {args.limit}")

    total_inserted = 0
    errors = 0
    for source in sources:
        inserted, status = collect_one(conn, source, inbox_id, args.limit)
        total_inserted += inserted
        if status == "error":
            errors += 1
        time.sleep(0.4)

    print(f"\ntotals: inserted={total_inserted} errors={errors}")
    conn.close()
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
