"""Read-only-ish SQLite query helper.

Why this exists: the Claude Code allowlist can't safely auto-approve
`python -c "..."` (arbitrary code execution), but it CAN auto-approve a
specific script. This script accepts a single SQL statement via argv or
stdin, runs it against the project DB, and prints results.

By default it refuses statements that look like writes (UPDATE/INSERT/
DELETE/DROP/CREATE/ALTER/REPLACE/PRAGMA …=). Pass --write to opt in for
those cases where you actually want a mutation; that path will still
prompt because Claude's allowlist only covers the read-only common case.

Usage:
    python query_db.py "SELECT COUNT(*) FROM sub_considerations"
    python query_db.py < my_query.sql
    python query_db.py --db other.db "SELECT 1"
    python query_db.py --write "UPDATE foo SET x=1"          # bypass safety
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = Path(os.environ.get("BESTPRACTICE_DB", str(ROOT / "data" / "bestpractice.db")))

WRITE_KEYWORDS = ("update ", "insert ", "delete ", "drop ", "create ",
                  "alter ", "replace ", "truncate ", "attach ", "detach ",
                  "vacuum")


def looks_mutating(sql: str) -> bool:
    s = sql.strip().lower()
    if not s:
        return False
    if any(s.startswith(k) for k in WRITE_KEYWORDS):
        return True
    # PRAGMA can be read or write; flag only assignment forms.
    if s.startswith("pragma") and "=" in s:
        return True
    return False


def render_rows(cursor) -> None:
    cols = [d[0] for d in cursor.description or []]
    rows = cursor.fetchall()
    if not cols:
        print(f"-- {cursor.rowcount} row(s) affected")
        return
    widths = [len(c) for c in cols]
    str_rows = []
    for r in rows:
        row = [("" if v is None else str(v)) for v in r]
        str_rows.append(row)
        widths = [max(w, len(v)) for w, v in zip(widths, row)]
    print(" | ".join(c.ljust(w) for c, w in zip(cols, widths)))
    print("-+-".join("-" * w for w in widths))
    for r in str_rows:
        print(" | ".join(v.ljust(w) for v, w in zip(r, widths)))
    print(f"-- {len(rows)} row(s)")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("sql", nargs="?", help="SQL statement (omit to read from stdin)")
    p.add_argument("--db", default=str(DEFAULT_DB), help="Path to SQLite DB")
    p.add_argument("--write", action="store_true",
                   help="Allow mutating statements (UPDATE/INSERT/DELETE/etc.)")
    args = p.parse_args()

    sql = args.sql if args.sql is not None else sys.stdin.read()
    sql = sql.strip()
    if not sql:
        print("error: no SQL given", file=sys.stderr)
        return 2

    if looks_mutating(sql) and not args.write:
        print("error: looks like a mutating statement; pass --write to confirm",
              file=sys.stderr)
        return 3

    conn = sqlite3.connect(args.db)
    try:
        cur = conn.execute(sql)
        render_rows(cur)
        if args.write:
            conn.commit()
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
