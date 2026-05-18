#!/usr/bin/env python3
"""Merge sub_considerations from a fixture file into existing scaffold cons.

Use when a page-type or component has scaffolded considerations (seeded by
init_db.seed_scaffolds / seed_site_wide_scaffolds / seed_category_scaffolds)
and you want to backfill real subs from a fixture without re-running
init_db.py from scratch.

Each fixture consideration is matched by (parent_type, parent_slug, slug)
to an existing row in `considerations`. Subs are inserted into
sub_considerations (idempotent on the UNIQUE(consideration_id, slug)), a
sub_consideration_placements row is added pointing the sub at its cons,
and phases are wired up. Honours the fixture's group_slug='site-wide'
rebucket the same way init_db.load_fixture does.

Usage:
    python scripts/load_subs_into_scaffolds.py fixtures/collection_page.json
    python scripts/load_subs_into_scaffolds.py fixtures/collection_page.json --apply
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bestpractice.db"


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def load(conn: sqlite3.Connection, fixture_path: Path, apply: bool) -> dict:
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    parent_type = data["parent_type"]
    parent_slug = data["parent_slug"]
    cur = conn.cursor()
    now = now_iso()

    stats = {
        "cons_matched": 0,
        "cons_missing": 0,
        "subs_inserted": 0,
        "subs_existed": 0,
        "placements_added": 0,
        "phases_added": 0,
    }

    for group in data["groups"]:
        effective_parent_slug = (
            "site-wide" if group["group_slug"] == "site-wide" else parent_slug
        )
        for cons in group["considerations"]:
            cons_row = cur.execute(
                "SELECT id FROM considerations WHERE parent_type=? AND parent_slug=? AND slug=?",
                (parent_type, effective_parent_slug, cons["slug"]),
            ).fetchone()
            if not cons_row:
                print(f"  [MISS] no scaffold for {parent_type}/{effective_parent_slug}/{cons['slug']!r}")
                stats["cons_missing"] += 1
                continue
            cons_id = cons_row[0]
            stats["cons_matched"] += 1

            for sub in cons["sub_considerations"]:
                existing = cur.execute(
                    "SELECT id FROM sub_considerations WHERE consideration_id=? AND slug=?",
                    (cons_id, sub["slug"]),
                ).fetchone()
                if existing:
                    sub_id = existing[0]
                    stats["subs_existed"] += 1
                    action = "exists"
                else:
                    action = "would-insert" if not apply else "insert"
                    sub_id = None
                    if apply:
                        cur.execute(
                            """INSERT INTO sub_considerations
                                   (consideration_id, slug, one_liner, body,
                                    source_name, source_suffix, source_title,
                                    source_url, source_date, status, display_order,
                                    created_at, last_updated)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,
                                       'approved', ?, ?, ?)""",
                            (cons_id, sub["slug"], sub["one_liner"], sub.get("body", ""),
                             sub.get("source_name", ""), sub.get("source_suffix", ""),
                             sub.get("source_title", ""), sub.get("source_url", ""),
                             sub.get("source_date"), sub["display_order"],
                             now, sub["last_updated"]),
                        )
                        sub_id = cur.lastrowid
                    stats["subs_inserted"] += 1

                print(f"  [{action}] {cons['slug']}/{sub['slug']}")

                # Placement (idempotent on PK sub_id+consideration_id)
                if apply and sub_id is not None:
                    cur.execute(
                        "INSERT OR IGNORE INTO sub_consideration_placements (sub_id, consideration_id, position) VALUES (?, ?, ?)",
                        (sub_id, cons_id, 1),
                    )
                    if cur.rowcount > 0:
                        stats["placements_added"] += 1
                    for pos, phase_slug in enumerate(sub.get("phases", []), start=1):
                        cur.execute(
                            "INSERT OR IGNORE INTO sub_consideration_phases (sub_consideration_id, phase_slug, position) VALUES (?, ?, ?)",
                            (sub_id, phase_slug, pos),
                        )
                        if cur.rowcount > 0:
                            stats["phases_added"] += 1

    if apply:
        # Rebuild FTS so new subs surface in /search immediately.
        cur.execute("DELETE FROM subs_fts")
        cur.execute(
            """INSERT INTO subs_fts (rowid, one_liner, body, cons_title, cons_intro)
               SELECT s.id, s.one_liner, s.body, c.title, c.intro
                 FROM sub_considerations s
                 JOIN considerations c ON c.id = s.consideration_id
                WHERE s.status='approved' AND c.status='approved'"""
        )
        conn.commit()

    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("fixture", help="Path to fixture JSON")
    parser.add_argument("--apply", action="store_true", help="Commit. Omit to dry-run.")
    parser.add_argument(
        "--db",
        default=os.environ.get("BESTPRACTICE_DB", str(DEFAULT_DB)),
        help=f"SQLite path (default: {DEFAULT_DB})",
    )
    args = parser.parse_args()

    fixture_path = Path(args.fixture)
    if not fixture_path.exists():
        print(f"fixture not found: {fixture_path}", file=sys.stderr)
        return 1
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"db not found: {db_path}", file=sys.stderr)
        return 1

    mode = "APPLY" if args.apply else "dry-run"
    print(f"[{mode}] fixture: {fixture_path}")
    print(f"[{mode}] db: {db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        stats = load(conn, fixture_path, apply=args.apply)
    finally:
        conn.close()
    print()
    for k, v in stats.items():
        print(f"  {k:>20}: {v}")
    if not args.apply:
        print("\nre-run with --apply to commit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
