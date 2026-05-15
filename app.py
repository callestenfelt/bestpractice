"""bestpractice — Flask app, Slice A (read surface only)."""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, abort, g, redirect, render_template, request, url_for

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("BESTPRACTICE_DB", str(ROOT / "data" / "bestpractice.db")))
NEW_WINDOW = timedelta(days=14)

app = Flask(__name__, root_path=str(ROOT))


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        if not DB_PATH.exists():
            sys.stderr.write(
                f"Database not found at {DB_PATH}. Run `python init_db.py` first.\n"
            )
            abort(500)
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.template_filter("is_new")
def is_new_filter(last_updated: str | None) -> bool:
    if not last_updated:
        return False
    try:
        dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
    except ValueError:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt) < NEW_WINDOW


def load_page_type_view(slug: str):
    db = get_db()
    page = db.execute(
        "SELECT slug, label, definition, schema_org_type FROM page_types WHERE slug = ?",
        (slug,),
    ).fetchone()
    if not page:
        abort(404)

    phases = db.execute(
        "SELECT slug, label FROM phases ORDER BY display_order"
    ).fetchall()

    cons_rows = db.execute(
        """SELECT id, slug, title, intro, group_label, group_slug, group_order, display_order
             FROM considerations
            WHERE parent_type = 'page_type' AND parent_slug = ? AND status = 'approved'
            ORDER BY group_order, display_order""",
        (slug,),
    ).fetchall()

    # Also pull site-wide considerations (special bucket) regardless of current page.
    if slug != "site-wide":
        sw_rows = db.execute(
            """SELECT id, slug, title, intro, group_label, group_slug, group_order, display_order
                 FROM considerations
                WHERE parent_type = 'page_type' AND parent_slug = 'site-wide' AND status = 'approved'
                ORDER BY group_order, display_order"""
        ).fetchall()
    else:
        sw_rows = []

    cons_ids = [r["id"] for r in cons_rows] + [r["id"] for r in sw_rows]
    subs_by_cons: dict[int, list[dict]] = {cid: [] for cid in cons_ids}
    if cons_ids:
        placeholders = ",".join("?" * len(cons_ids))
        sub_rows = db.execute(
            f"""SELECT id, consideration_id, slug, one_liner, body,
                       source_name, source_suffix, source_title, source_url, source_date,
                       last_updated, display_order
                  FROM sub_considerations
                 WHERE status = 'approved' AND consideration_id IN ({placeholders})
                 ORDER BY consideration_id, display_order""",
            cons_ids,
        ).fetchall()
        sub_ids = [r["id"] for r in sub_rows]
        phases_by_sub: dict[int, list[str]] = {sid: [] for sid in sub_ids}
        if sub_ids:
            ph_placeholders = ",".join("?" * len(sub_ids))
            for row in db.execute(
                f"""SELECT sub_consideration_id, phase_slug
                      FROM sub_consideration_phases
                     WHERE sub_consideration_id IN ({ph_placeholders})
                     ORDER BY sub_consideration_id, position""",
                sub_ids,
            ).fetchall():
                phases_by_sub[row["sub_consideration_id"]].append(row["phase_slug"])

        cons_slug_by_id = {r["id"]: r["slug"] for r in cons_rows + list(sw_rows)}
        for r in sub_rows:
            subs_by_cons[r["consideration_id"]].append({
                "slug": r["slug"],
                "cons_slug": cons_slug_by_id[r["consideration_id"]],
                "one_liner": r["one_liner"],
                "body": r["body"],
                "source_name": r["source_name"],
                "source_suffix": r["source_suffix"],
                "source_title": r["source_title"],
                "source_url": r["source_url"],
                "source_date": r["source_date"],
                "last_updated": r["last_updated"],
                "phases": phases_by_sub.get(r["id"], []),
            })

    def build_groups(rows):
        groups: list[dict] = []
        current = None
        for r in rows:
            key = (r["group_order"], r["group_slug"])
            if not current or current["_key"] != key:
                current = {
                    "_key": key,
                    "group_slug": r["group_slug"],
                    "group_label": r["group_label"],
                    "group_order": r["group_order"],
                    "considerations": [],
                }
                groups.append(current)
            current["considerations"].append({
                "slug": r["slug"],
                "title": r["title"],
                "intro": r["intro"],
                "sub_considerations": subs_by_cons.get(r["id"], []),
            })
        return groups

    groups = build_groups(cons_rows)
    if sw_rows:
        # Site-wide always renders as one trailing group with `hidden`; collapse all
        # its considerations into a single group regardless of group_label in the DB.
        sw_subs = []
        for r in sw_rows:
            sw_subs.append({
                "slug": r["slug"],
                "title": r["title"],
                "intro": r["intro"],
                "sub_considerations": subs_by_cons.get(r["id"], []),
            })
        groups.append({
            "group_slug": "site-wide",
            "group_label": "Site-wide considerations",
            "group_order": 999,
            "considerations": sw_subs,
        })

    return page, phases, groups


@app.route("/")
def home():
    return redirect(url_for("page_type", slug="article-page"))


@app.route("/page-type/<slug>")
def page_type(slug):
    page, phases, groups = load_page_type_view(slug)
    return render_template("page_type.html", page=page, phases=phases, groups=groups)


@app.route("/search")
def search():
    return render_template(
        "placeholder.html",
        heading="Search",
        message="Search lands in a later slice. The header form already points here so it's wired when the route comes online.",
        q=request.args.get("q", ""),
    )


@app.route("/admin/queue")
def admin_queue():
    return render_template(
        "placeholder.html",
        heading="Review queue",
        message="Admin queue lands in a later slice. Ingestion + Groq scoring write pending items here for approval.",
    )


@app.route("/admin/sources")
def admin_sources():
    return render_template(
        "placeholder.html",
        heading="Sources",
        message="Source management lands in a later slice. RSS + structured feeds will be configured here.",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5681, debug=False)
