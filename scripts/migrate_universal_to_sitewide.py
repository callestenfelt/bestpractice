#!/usr/bin/env python3
"""Move article-page's universal considerations to the shared site-wide bucket.

The article-page fixture seeded `url-structure`, `page-title-h1`,
`meta-description` directly on the article-page page_type. These three are
genuinely universal (every indexable page has a URL, a title, a meta
description) — so they should live on `site-wide` and overlay every other
page_type via the existing site-wide layering in load_parent_view().

This is a one-shot, idempotent migration. Re-running is a no-op once each
target consideration is already on site-wide. Sub-consideration placements
are keyed by consideration_id and don't need to move.

Usage:
    python scripts/migrate_universal_to_sitewide.py           # dry-run
    python scripts/migrate_universal_to_sitewide.py --apply   # commit
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bestpractice.db"

# (source_parent_slug, cons_slug) — the migrator finds these by
# (parent_type='page_type', parent_slug=source_parent_slug, slug=cons_slug)
# and moves them to (page_type, site-wide). Extend the list if more
# universal considerations later get mis-seeded on a specific page_type.
UNIVERSAL_PROMOTIONS: list[tuple[str, str]] = [
    ("article-page", "url-structure"),
    ("article-page", "page-title-h1"),
    ("article-page", "meta-description"),
]


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def migrate(conn: sqlite3.Connection, apply: bool) -> int:
    cur = conn.cursor()
    moved = 0
    now = now_iso()
    for src_slug, cons_slug in UNIVERSAL_PROMOTIONS:
        row = cur.execute(
            """SELECT id, parent_slug, group_label, group_slug, group_order
                 FROM considerations
                WHERE parent_type='page_type' AND slug=?
                  AND parent_slug IN (?, 'site-wide')""",
            (cons_slug, src_slug),
        ).fetchone()
        if row is None:
            print(f"  [skip] slug={cons_slug!r} not found on {src_slug!r} or site-wide")
            continue
        cons_id, current_slug, group_label, group_slug, group_order = row
        if current_slug == "site-wide":
            print(f"  [ok]   slug={cons_slug!r} already on site-wide (id={cons_id})")
            continue
        print(
            f"  [move] slug={cons_slug!r} id={cons_id} : "
            f"{current_slug!r} -> 'site-wide' "
            f"(was group {group_label!r}/{group_slug!r} order {group_order})"
        )
        moved += 1
        if not apply:
            continue
        # 1. Update the legacy parent pointer + group identity on the
        #    consideration row itself. The read view groups site-wide cons
        #    under a single trailing "Site-wide considerations" overlay
        #    regardless of group_label, but normalising the columns keeps
        #    /page-type/site-wide tidy and matches the seed_site_wide_scaffolds
        #    convention (group_label='Site-wide considerations',
        #    group_slug='site-wide', group_order=6).
        cur.execute(
            """UPDATE considerations
                  SET parent_slug='site-wide',
                      group_label='Site-wide considerations',
                      group_slug='site-wide',
                      group_order=6,
                      updated_at=?
                WHERE id=?""",
            (now, cons_id),
        )
        # 2. Swap the destination row. DELETE the old article-page pointer
        #    (if present) and INSERT a site-wide one. INSERT OR IGNORE
        #    handles the case where a destination already pointed at
        #    site-wide for some reason (manual edit, partial prior run).
        cur.execute(
            """DELETE FROM consideration_destinations
                WHERE consideration_id=? AND dest_kind='page_type' AND dest_slug=?""",
            (cons_id, src_slug),
        )
        cur.execute(
            """INSERT OR IGNORE INTO consideration_destinations
                   (consideration_id, dest_kind, dest_slug)
               VALUES (?, 'page_type', 'site-wide')""",
            (cons_id,),
        )
    if apply:
        conn.commit()
    return moved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Commit changes. Omit to dry-run.",
    )
    parser.add_argument(
        "--db",
        default=os.environ.get("BESTPRACTICE_DB", str(DEFAULT_DB)),
        help=f"SQLite path (default: {DEFAULT_DB})",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"db not found: {db_path}", file=sys.stderr)
        return 1

    mode = "APPLY" if args.apply else "dry-run"
    print(f"[{mode}] db: {db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        moved = migrate(conn, apply=args.apply)
    finally:
        conn.close()
    verb = "moved" if args.apply else "would move"
    print(f"{verb} {moved} consideration(s)")
    if not args.apply and moved:
        print("re-run with --apply to commit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
