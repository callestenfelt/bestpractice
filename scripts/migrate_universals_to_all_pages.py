#!/usr/bin/env python3
"""Move per-page universals out of the trailing Site-wide bucket into the
`all-pages` category, so they render inline on every page-type in their
natural group and disappear from component views.

Background (Session 19 → 20):
- `site-wide` was overloaded: a page_type row AND a destination class AND a
  hardcoded render bucket forced to `group_label='Site-wide considerations'`,
  `group_order=999`. So URL structure + Page title + Meta description got
  pushed to the bottom of every page render even though their natural home
  is "Before you start" / "Top of page" / "Behind the scenes".
- The site-wide overlay also leaked onto /component/<slug> renders, which
  was unintended — those cons describe pages, not buttons or modals.
- Solution: introduce an `all-pages` page_type_category (every real
  page-type as a member) and move the four per-page universals onto it.
  Cons destined via category render inline (`load_parent_view` query
  pulls them into `cons_rows`, not the `sw_rows` overlay), so they take
  the group_label/order on their own row.

Cons moved by this script:
  url-structure     -> "Before you start" / display_order=3
  page-title-h1     -> "Top of page"      / display_order=1
  meta-description  -> "Behind the scenes" / display_order=1
  sw-seo            -> "Behind the scenes" / display_order=4

Idempotent: re-running is a no-op once a cons is already attached to
`all-pages`. Run `python3 init_db.py` first to ensure the `all-pages`
category exists in `page_type_categories` + memberships.

Usage:
    python scripts/migrate_universals_to_all_pages.py           # dry-run
    python scripts/migrate_universals_to_all_pages.py --apply   # commit
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

# (cons_slug, group_label, group_slug, group_order, display_order)
# group_order is shared with the page-type's own group structure
# (Before you start=1, Top of page=2, Body=3, End of page=4,
#  Behind the scenes=5). Picked so each universal lands in its
# natural place on every page render.
PROMOTIONS: list[tuple[str, str, str, int, int]] = [
    ("url-structure",     "Before you start",  "before-you-start",  1, 3),
    ("page-title-h1",     "Top of page",       "top-of-page",       2, 1),
    ("meta-description",  "Behind the scenes", "behind-the-scenes", 5, 1),
    ("sw-seo",            "Behind the scenes", "behind-the-scenes", 5, 4),
]


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def category_exists(cur: sqlite3.Cursor, slug: str) -> bool:
    row = cur.execute(
        "SELECT 1 FROM page_type_categories WHERE slug=?", (slug,)
    ).fetchone()
    return row is not None


def migrate(conn: sqlite3.Connection, apply: bool) -> int:
    cur = conn.cursor()
    if not category_exists(cur, "all-pages"):
        print("  [abort] page_type_categories has no 'all-pages' row. Run python3 init_db.py first.")
        return 0
    moved = 0
    now = now_iso()
    for cons_slug, group_label, group_slug, group_order, display_order in PROMOTIONS:
        row = cur.execute(
            """SELECT id, parent_slug, group_label, group_slug, group_order, display_order
                 FROM considerations
                WHERE slug=?
                  AND parent_type='page_type'
                  AND parent_slug IN ('site-wide', 'category:all-pages')""",
            (cons_slug,),
        ).fetchone()
        if row is None:
            print(f"  [skip] slug={cons_slug!r} not found on site-wide or category:all-pages")
            continue
        cons_id, current_parent, cur_gl, cur_gs, cur_go, cur_do = row
        already_attached = cur.execute(
            """SELECT 1 FROM consideration_destinations
                WHERE consideration_id=? AND dest_kind='category' AND dest_slug='all-pages'""",
            (cons_id,),
        ).fetchone() is not None
        target_already = (
            current_parent == "category:all-pages"
            and already_attached
            and cur_gl == group_label
            and cur_gs == group_slug
            and cur_go == group_order
            and cur_do == display_order
        )
        if target_already:
            print(f"  [ok]   slug={cons_slug!r} id={cons_id} already on all-pages / {group_label}#{display_order}")
            continue
        print(
            f"  [move] slug={cons_slug!r} id={cons_id} : "
            f"parent={current_parent!r} group={cur_gl!r}/{cur_gs!r} order={cur_go}.{cur_do} "
            f"-> parent='category:all-pages' group={group_label!r}/{group_slug!r} order={group_order}.{display_order}"
        )
        moved += 1
        if not apply:
            continue
        cur.execute(
            """UPDATE considerations
                  SET parent_slug='category:all-pages',
                      group_label=?, group_slug=?, group_order=?, display_order=?,
                      updated_at=?
                WHERE id=?""",
            (group_label, group_slug, group_order, display_order, now, cons_id),
        )
        cur.execute(
            """DELETE FROM consideration_destinations
                WHERE consideration_id=? AND dest_kind='page_type' AND dest_slug='site-wide'""",
            (cons_id,),
        )
        cur.execute(
            """INSERT OR IGNORE INTO consideration_destinations
                   (consideration_id, dest_kind, dest_slug)
               VALUES (?, 'category', 'all-pages')""",
            (cons_id,),
        )
    if apply:
        conn.commit()
    return moved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true", help="Commit changes. Omit to dry-run.")
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
