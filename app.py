"""bestpractice — Flask app."""
from __future__ import annotations

import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, g, redirect, render_template, request, url_for

load_dotenv()

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("BESTPRACTICE_DB", str(ROOT / "data" / "bestpractice.db")))
NEW_WINDOW = timedelta(days=14)

app = Flask(__name__, root_path=str(ROOT))
# Single-user admin tool; cheap to revalidate. Avoids the 12-hour stale-cache
# window where users see old JS/CSS after a deploy until they hard-refresh.
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# Bumped on every process start (deploy restarts the service). Used as
# ?v=... on static asset URLs so a deploy guarantees a cache-miss even if
# the browser still has the old asset under the un-bumped URL.
ASSET_VERSION = str(int(time.time()))


@app.context_processor
def _inject_asset_helper():
    def asset(filename: str) -> str:
        return url_for("static", filename=filename, v=ASSET_VERSION)
    return {"asset": asset}


@app.context_processor
def _inject_nav():
    """Sidebar nav data for every render: all page types + components in
    display_order, each tagged with whether it has at least one approved
    sub-consideration whose last_updated is within the 14-day "new" window.
    Also injects current_kind and current_slug so the sidebar can mark the
    active link via aria-current="page" from inside base.html.
    """
    db = get_db()
    cutoff = (datetime.now(timezone.utc) - NEW_WINDOW).isoformat(timespec="seconds").replace("+00:00", "Z")
    # EXISTS subquery: any approved sub under this parent updated within window.
    nav_query = """
        SELECT t.slug, t.label, t.icon,
               EXISTS(
                   SELECT 1 FROM sub_considerations s
                   JOIN considerations c ON c.id = s.consideration_id
                   WHERE c.parent_type = ?
                     AND c.parent_slug = t.slug
                     AND s.status = 'approved'
                     AND c.status = 'approved'
                     AND s.last_updated >= ?
               ) AS has_new
          FROM {table} t
         ORDER BY t.display_order
    """
    nav_page_types = db.execute(
        nav_query.format(table="page_types"), ("page_type", cutoff)
    ).fetchall()
    nav_components = db.execute(
        nav_query.format(table="components"), ("component", cutoff)
    ).fetchall()

    # Active-link inference from the current request endpoint.
    current_kind = None
    current_slug = None
    if request.endpoint == "page_type":
        current_kind = "page_type"
        current_slug = request.view_args.get("slug") if request.view_args else None
    elif request.endpoint == "component":
        current_kind = "component"
        current_slug = request.view_args.get("slug") if request.view_args else None

    return {
        "nav_page_types": nav_page_types,
        "nav_components": nav_components,
        "current_kind": current_kind,
        "current_slug": current_slug,
    }


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


def load_parent_view(parent_type: str, parent_slug: str):
    """Build the read-view payload for a page_type OR component parent.

    Returns (page, parent_kind_label, phases, groups). `page` is a dict with
    {slug, label, definition, schema_org_type} — schema_org_type is None for
    components. Site-wide considerations are always appended as a trailing
    hidden group unless the requested parent IS the site-wide bucket itself.
    """
    if parent_type not in ("page_type", "component"):
        abort(404)
    db = get_db()
    if parent_type == "page_type":
        row = db.execute(
            "SELECT slug, label, definition, schema_org_type, icon FROM page_types WHERE slug = ?",
            (parent_slug,),
        ).fetchone()
        parent_kind_label = "Page type"
    else:
        row = db.execute(
            "SELECT slug, label, definition, icon FROM components WHERE slug = ?",
            (parent_slug,),
        ).fetchone()
        parent_kind_label = "Component"
    if not row:
        abort(404)
    page = {
        "slug": row["slug"],
        "label": row["label"],
        "definition": row["definition"],
        "icon": row["icon"],
        "schema_org_type": row["schema_org_type"] if parent_type == "page_type" else None,
    }

    phases = db.execute(
        "SELECT slug, label FROM phases ORDER BY display_order"
    ).fetchall()

    # Considerations destined to this parent — directly (dest_kind matches the
    # parent_type, dest_slug matches the parent_slug) OR via a category that
    # contains this page_type. The Session 12 consideration_destinations
    # join is the authoritative source; the legacy parent_type/parent_slug
    # columns are kept for migration backward-compat but no longer queried.
    if parent_type == "page_type":
        cons_rows = db.execute(
            """SELECT DISTINCT c.id, c.slug, c.title, c.intro,
                               c.group_label, c.group_slug, c.group_order, c.display_order
                 FROM considerations c
                 JOIN consideration_destinations d ON d.consideration_id = c.id
            LEFT JOIN page_type_in_category pic ON d.dest_kind = 'category'
                                              AND d.dest_slug = pic.category_slug
                WHERE c.status = 'approved'
                  AND (   (d.dest_kind = 'page_type' AND d.dest_slug = ?)
                       OR (d.dest_kind = 'category'  AND pic.page_type_slug = ?))
                ORDER BY c.group_order, c.display_order""",
            (parent_slug, parent_slug),
        ).fetchall()
    else:
        cons_rows = db.execute(
            """SELECT DISTINCT c.id, c.slug, c.title, c.intro,
                               c.group_label, c.group_slug, c.group_order, c.display_order
                 FROM considerations c
                 JOIN consideration_destinations d ON d.consideration_id = c.id
                WHERE c.status = 'approved'
                  AND d.dest_kind = 'component' AND d.dest_slug = ?
                ORDER BY c.group_order, c.display_order""",
            (parent_slug,),
        ).fetchall()

    # Site-wide remains a special page_type bucket: any consideration destined
    # to (page_type, site-wide) layers onto every other parent's view as a
    # trailing group. The category mechanism doesn't change this — a
    # consideration that's only attached to a category (not site-wide) won't
    # show in the overlay; it'll show directly on the matching pages.
    is_sitewide_self = parent_type == "page_type" and parent_slug == "site-wide"
    if not is_sitewide_self:
        already_ids = {r["id"] for r in cons_rows}
        sw_rows_raw = db.execute(
            """SELECT DISTINCT c.id, c.slug, c.title, c.intro,
                               c.group_label, c.group_slug, c.group_order, c.display_order
                 FROM considerations c
                 JOIN consideration_destinations d ON d.consideration_id = c.id
                WHERE c.status = 'approved'
                  AND d.dest_kind = 'page_type' AND d.dest_slug = 'site-wide'
                ORDER BY c.group_order, c.display_order"""
        ).fetchall()
        # De-dupe: if a consideration is already in cons_rows (via direct or
        # category match), don't double-render it in the overlay.
        sw_rows = [r for r in sw_rows_raw if r["id"] not in already_ids]
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

    return page, parent_kind_label, phases, groups


@app.route("/")
def home():
    return redirect(url_for("page_type", slug="article-page"))


@app.route("/page-type/<slug>")
def page_type(slug):
    page, parent_kind, phases, groups = load_parent_view("page_type", slug)
    return render_template(
        "page_type.html",
        page=page,
        parent_kind=parent_kind,
        phases=phases,
        groups=groups,
        is_self_sitewide=(slug == "site-wide"),
    )


@app.route("/component/<slug>")
def component(slug):
    page, parent_kind, phases, groups = load_parent_view("component", slug)
    return render_template(
        "page_type.html",
        page=page,
        parent_kind=parent_kind,
        phases=phases,
        groups=groups,
        is_self_sitewide=False,
    )


def _fts_quote(term: str) -> str:
    return '"' + term.replace('"', '""') + '"'


def expand_synonyms(db: sqlite3.Connection, q: str) -> list[str]:
    """Return alternative search terms derived from the synonyms table.

    Matches the whole query case-insensitively against (a) synonym text and
    (b) entity labels (page_types, components, phases). For each hit, adds
    the entity's other names (label + other synonyms) as expansions. The
    user's own query is never returned as an expansion.
    """
    q_lower = q.lower()
    expansions: set[str] = set()
    matched_entities: set[tuple[str, str]] = set()

    for row in db.execute(
        "SELECT entity_type, entity_slug FROM synonyms WHERE LOWER(synonym) = ?",
        (q_lower,),
    ).fetchall():
        matched_entities.add((row["entity_type"], row["entity_slug"]))

    for table, etype in (("page_types", "page_type"), ("components", "component"), ("phases", "phase")):
        for row in db.execute(
            f"SELECT slug FROM {table} WHERE LOWER(label) = ?", (q_lower,)
        ).fetchall():
            matched_entities.add((etype, row["slug"]))

    for etype, eslug in matched_entities:
        table = {"page_type": "page_types", "component": "components", "phase": "phases"}[etype]
        label_row = db.execute(
            f"SELECT label FROM {table} WHERE slug = ?", (eslug,)
        ).fetchone()
        if label_row and label_row["label"].lower() != q_lower:
            expansions.add(label_row["label"])
        for syn_row in db.execute(
            "SELECT synonym FROM synonyms WHERE entity_type = ? AND entity_slug = ?",
            (etype, eslug),
        ).fetchall():
            if syn_row["synonym"].lower() != q_lower:
                expansions.add(syn_row["synonym"])

    return sorted(expansions, key=str.lower)


def run_search(db: sqlite3.Connection, q: str):
    expansions = expand_synonyms(db, q)
    match_parts = [_fts_quote(q)] + [_fts_quote(e) for e in expansions]
    match_expr = " OR ".join(match_parts)

    rows = db.execute(
        """SELECT s.id, s.slug, s.one_liner,
                  c.slug AS cons_slug, c.title AS cons_title,
                  c.parent_type, c.parent_slug, c.group_label,
                  snippet(subs_fts, 1, '<mark>', '</mark>', '…', 18) AS body_snippet,
                  snippet(subs_fts, 0, '<mark>', '</mark>', '…', 12) AS one_liner_snippet
             FROM subs_fts
             JOIN sub_considerations s ON s.id = subs_fts.rowid
             JOIN considerations c ON c.id = s.consideration_id
            WHERE subs_fts MATCH ?
              AND s.status = 'approved'
              AND c.status = 'approved'
            ORDER BY rank""",
        (match_expr,),
    ).fetchall()

    # Resolve human labels for parents (page types, components).
    page_type_labels = {r["slug"]: (r["label"], r["display_order"]) for r in db.execute(
        "SELECT slug, label, display_order FROM page_types"
    ).fetchall()}
    component_labels = {r["slug"]: (r["label"], r["display_order"]) for r in db.execute(
        "SELECT slug, label, display_order FROM components"
    ).fetchall()}

    def group_key(row):
        ptype = row["parent_type"]
        pslug = row["parent_slug"]
        if ptype == "page_type":
            label, order = page_type_labels.get(pslug, (pslug, 999))
            # Site-wide is rendered as its own kind, ordered after page types.
            if pslug == "site-wide":
                return ("site-wide", pslug, "Site-wide", "Cross-cutting", 10_000)
            return ("page_type", pslug, label, "Page type", order)
        if ptype == "component":
            label, order = component_labels.get(pslug, (pslug, 999))
            return ("component", pslug, label, "Component", 1_000 + order)
        return ("other", pslug, pslug, "", 100_000)

    groups: dict[tuple, dict] = {}
    for r in rows:
        kind, pslug, plabel, kind_label, order = group_key(r)
        key = (order, kind, pslug)
        if key not in groups:
            groups[key] = {
                "kind": kind,
                "kind_label": kind_label,
                "parent_slug": pslug,
                "parent_label": plabel,
                "results": [],
            }
        # Prefer the body snippet when FTS injected a highlight there;
        # otherwise fall back to the one-liner snippet, otherwise the
        # raw one-liner. Snippet() returns the text with no <mark> when
        # the column had no hits.
        body_snip = r["body_snippet"]
        ol_snip = r["one_liner_snippet"]
        has_body_hit = "<mark>" in (body_snip or "")
        snippet = body_snip if has_body_hit else ol_snip
        groups[key]["results"].append({
            "cons_slug": r["cons_slug"],
            "sub_slug": r["slug"],
            "cons_title": r["cons_title"],
            "group_label": r["group_label"],
            "one_liner": r["one_liner"],
            "one_liner_html": ol_snip if "<mark>" in (ol_snip or "") else r["one_liner"],
            "snippet": snippet,
            "parent_label": plabel,
        })

    ordered_groups = [groups[k] for k in sorted(groups.keys())]
    total = len(rows)
    page_type_hits = sum(1 for g in ordered_groups if g["kind"] == "page_type")
    component_hits = sum(1 for g in ordered_groups if g["kind"] == "component")
    return ordered_groups, total, page_type_hits, component_hits, expansions


@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return render_template(
            "search.html",
            q="",
            groups=[],
            total=0,
            page_type_hits=0,
            component_hits=0,
            expansions=[],
        )
    db = get_db()
    try:
        groups, total, pt_hits, comp_hits, expansions = run_search(db, q)
    except sqlite3.OperationalError:
        # FTS rejects some special-char inputs; treat as no results rather
        # than 500ing the page.
        groups, total, pt_hits, comp_hits, expansions = [], 0, 0, 0, []
    return render_template(
        "search.html",
        q=q,
        groups=groups,
        total=total,
        page_type_hits=pt_hits,
        component_hits=comp_hits,
        expansions=expansions,
    )


def _format_relative(iso: str | None) -> str:
    if not iso:
        return "never"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return iso
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    s = int((datetime.now(timezone.utc) - dt).total_seconds())
    if s < 60:
        return "just now"
    if s < 3600:
        return f"{s // 60}m ago"
    if s < 86400:
        return f"{s // 3600}h ago"
    d = s // 86400
    if d == 1:
        return "yesterday"
    if d < 7:
        return f"{d}d ago"
    return dt.date().isoformat()


def load_queue_view(db: sqlite3.Connection):
    rows = db.execute(
        """SELECT s.id, s.slug, s.one_liner, s.body, s.relevance_score,
                  s.source_name, s.source_date, s.source_url, s.source_title,
                  c.slug AS cons_slug, c.title AS cons_title,
                  c.parent_type, c.parent_slug, c.group_label
             FROM sub_considerations s
             JOIN considerations c ON c.id = s.consideration_id
            WHERE s.status = 'pending'
            ORDER BY COALESCE(s.relevance_score, 0) DESC, s.created_at DESC"""
    ).fetchall()

    sub_ids = [r["id"] for r in rows]
    phases_by_sub: dict[int, list[str]] = {sid: [] for sid in sub_ids}
    if sub_ids:
        ph = ",".join("?" * len(sub_ids))
        for row in db.execute(
            f"""SELECT sub_consideration_id, phase_slug
                  FROM sub_consideration_phases
                 WHERE sub_consideration_id IN ({ph})
                 ORDER BY sub_consideration_id, position""",
            sub_ids,
        ).fetchall():
            phases_by_sub[row["sub_consideration_id"]].append(row["phase_slug"])

    page_types = {r["slug"]: r["label"] for r in db.execute(
        "SELECT slug, label FROM page_types"
    ).fetchall()}
    components = {r["slug"]: r["label"] for r in db.execute(
        "SELECT slug, label FROM components"
    ).fetchall()}

    items = []
    for r in rows:
        if r["parent_type"] == "page_type":
            parent_label = page_types.get(r["parent_slug"], r["parent_slug"])
        else:
            parent_label = components.get(r["parent_slug"], r["parent_slug"])
        bits = [parent_label]
        if r["group_label"]:
            bits.append(r["group_label"])
        bits.append(r["cons_title"])
        items.append({
            "id": r["id"],
            "slug": r["slug"],
            "one_liner": r["one_liner"],
            "body": r["body"],
            "score": r["relevance_score"],
            "source_name": r["source_name"],
            "source_date": r["source_date"],
            "source_url": r["source_url"],
            "source_title": r["source_title"],
            "phases": phases_by_sub.get(r["id"], []),
            "cons_breadcrumb": " · ".join(bits),
        })

    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    approved_week = db.execute(
        "SELECT COUNT(*) FROM sub_considerations WHERE status='approved' AND last_updated >= ?",
        (week_ago,),
    ).fetchone()[0]
    rejected_count = db.execute(
        "SELECT COUNT(*) FROM sub_considerations WHERE status='rejected'"
    ).fetchone()[0]

    last_sync_row = db.execute(
        "SELECT MAX(last_collected) AS lc FROM sources WHERE status='active'"
    ).fetchone()
    last_sync = _format_relative(last_sync_row["lc"] if last_sync_row else None)

    return {
        "items": items,
        "pending_count": len(items),
        "approved_week": approved_week,
        "rejected_count": rejected_count,
        "last_sync": last_sync,
    }


def load_queue_catalog(db: sqlite3.Connection):
    """Picker data for the edit-and-approve dialog:

    - cons_options: every approved consideration (excluding ingest-inbox),
      labeled by parent. Used by the single "Destination consideration" picker.
    - cons_destinations: { consideration_id: [{kind, slug, label}] } so the
      dialog can pre-populate the destinations checkboxes with the chosen
      consideration's current destinations when the user picks one.
    - dest_palette: { categories: [{slug,label}], page_types: [...], components: [...] }
      — the full set of available destinations to render as checkboxes.
    - phases: the canonical phase list."""
    rows = db.execute(
        """SELECT c.id, c.title, c.parent_type, c.parent_slug, c.group_label,
                  COALESCE(pt.label, cmp.label) AS parent_label,
                  COALESCE(pt.display_order, cmp.display_order, 999) AS parent_order,
                  c.group_order, c.display_order
             FROM considerations c
        LEFT JOIN page_types pt ON c.parent_type='page_type' AND pt.slug=c.parent_slug
        LEFT JOIN components cmp ON c.parent_type='component' AND cmp.slug=c.parent_slug
            WHERE c.status='approved' AND c.slug != 'ingest-inbox'
            ORDER BY c.parent_type, parent_order, c.group_order, c.display_order"""
    ).fetchall()
    cons_options = [{
        "id": r["id"],
        "label": (f"{r['parent_label']} · {r['group_label']} → {r['title']}"
                  if r["group_label"] else f"{r['parent_label']} → {r['title']}"),
    } for r in rows]

    # Per-consideration current destinations, keyed by id. JS reads this
    # when the user picks a consideration so the checkboxes reflect what
    # destinations that consideration is currently attached to.
    cons_destinations: dict[int, list[dict]] = {r["id"]: [] for r in rows}
    for d in db.execute(
        """SELECT consideration_id, dest_kind, dest_slug
             FROM consideration_destinations
            WHERE consideration_id IN (SELECT id FROM considerations
                                        WHERE status='approved' AND slug!='ingest-inbox')"""
    ).fetchall():
        cons_destinations.setdefault(d["consideration_id"], []).append({
            "kind": d["dest_kind"], "slug": d["dest_slug"],
        })

    # Destination palette: every checkbox the dialog might render.
    categories = [{"slug": r["slug"], "label": r["label"]} for r in db.execute(
        "SELECT slug, label FROM page_type_categories ORDER BY display_order"
    ).fetchall()]
    page_types_pal = [{"slug": r["slug"], "label": r["label"]} for r in db.execute(
        "SELECT slug, label FROM page_types ORDER BY display_order"
    ).fetchall()]
    components_pal = [{"slug": r["slug"], "label": r["label"]} for r in db.execute(
        "SELECT slug, label FROM components ORDER BY display_order"
    ).fetchall()]
    dest_palette = {
        "categories": categories,
        "page_types": page_types_pal,
        "components": components_pal,
    }

    phases = db.execute(
        "SELECT slug, label FROM phases ORDER BY display_order"
    ).fetchall()
    return cons_options, cons_destinations, dest_palette, phases


@app.route("/admin/queue")
def admin_queue():
    db = get_db()
    view = load_queue_view(db)
    cons_options, cons_destinations, dest_palette, all_phases = load_queue_catalog(db)
    view["cons_options"] = cons_options
    view["cons_destinations"] = cons_destinations
    view["dest_palette"] = dest_palette
    view["all_phases"] = all_phases
    view["error"] = request.args.get("error", "").strip()
    return render_template("admin/queue.html", **view)


def _sync_fts_row(db: sqlite3.Connection, sub_id: int) -> None:
    """Re-insert a sub_consideration into subs_fts (rowid keyed). Called
    after approve/edit_approve so search picks the new copy up. DELETE+
    INSERT is safe for both first-approve and re-edit."""
    db.execute("DELETE FROM subs_fts WHERE rowid = ?", (sub_id,))
    db.execute(
        """INSERT INTO subs_fts (rowid, one_liner, body, cons_title, cons_intro)
           SELECT s.id, s.one_liner, s.body, c.title, c.intro
             FROM sub_considerations s
             JOIN considerations c ON c.id = s.consideration_id
            WHERE s.id = ? AND s.status='approved' AND c.status='approved'""",
        (sub_id,),
    )


def _ensure_pending(db: sqlite3.Connection, sub_id: int) -> sqlite3.Row:
    row = db.execute(
        "SELECT id, status FROM sub_considerations WHERE id = ?", (sub_id,)
    ).fetchone()
    if not row:
        abort(404)
    if row["status"] != "pending":
        # Idempotent: already-acted-on rows redirect quietly rather than 409ing.
        return None
    return row


@app.route("/admin/queue/<int:sub_id>/approve", methods=["POST"])
def admin_queue_approve(sub_id):
    db = get_db()
    if _ensure_pending(db, sub_id) is None:
        return redirect(url_for("admin_queue"))
    db.execute(
        "UPDATE sub_considerations SET status='approved', last_updated=? WHERE id=?",
        (datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"), sub_id),
    )
    _sync_fts_row(db, sub_id)
    db.commit()
    return redirect(url_for("admin_queue"))


@app.route("/admin/queue/<int:sub_id>/reject", methods=["POST"])
def admin_queue_reject(sub_id):
    db = get_db()
    if _ensure_pending(db, sub_id) is None:
        return redirect(url_for("admin_queue"))
    db.execute(
        "UPDATE sub_considerations SET status='rejected', last_updated=? WHERE id=?",
        (datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"), sub_id),
    )
    db.commit()
    return redirect(url_for("admin_queue"))


@app.route("/admin/queue/<int:sub_id>/edit_approve", methods=["POST"])
def admin_queue_edit_approve(sub_id):
    db = get_db()
    if _ensure_pending(db, sub_id) is None:
        return redirect(url_for("admin_queue"))

    one_liner = (request.form.get("one_liner") or "").strip()
    body_text = (request.form.get("body") or "").strip()
    source_url = (request.form.get("source_url") or "").strip()
    source_date = (request.form.get("source_date") or "").strip() or None
    cons_id_raw = request.form.get("consideration_id") or ""
    phase_slugs = request.form.getlist("phase")

    if not one_liner:
        return redirect(url_for("admin_queue", error="One-liner is required."))
    try:
        cons_id = int(cons_id_raw)
    except ValueError:
        return redirect(url_for("admin_queue", error="Pick a destination consideration."))
    cons_row = db.execute(
        "SELECT id FROM considerations WHERE id = ? AND status='approved' AND slug != 'ingest-inbox'",
        (cons_id,),
    ).fetchone()
    if not cons_row:
        return redirect(url_for("admin_queue", error="Unknown consideration."))

    valid_phases = {r["slug"] for r in db.execute("SELECT slug FROM phases").fetchall()}
    phase_slugs = [p for p in phase_slugs if p in valid_phases]

    # Destinations: form fields named "dest_category", "dest_page_type",
    # "dest_component" each carry slug values. Validate against the actual
    # taxonomy tables before writing. If the user didn't submit any of
    # these, leave the consideration's destinations unchanged.
    submitted_dests = (
        bool(request.form.getlist("dest_category"))
        or bool(request.form.getlist("dest_page_type"))
        or bool(request.form.getlist("dest_component"))
    )
    valid_cats = {r["slug"] for r in db.execute("SELECT slug FROM page_type_categories").fetchall()}
    valid_pts = {r["slug"] for r in db.execute("SELECT slug FROM page_types").fetchall()}
    valid_comps = {r["slug"] for r in db.execute("SELECT slug FROM components").fetchall()}
    new_dests: list[tuple[str, str]] = []
    for s in request.form.getlist("dest_category"):
        if s in valid_cats: new_dests.append(("category", s))
    for s in request.form.getlist("dest_page_type"):
        if s in valid_pts: new_dests.append(("page_type", s))
    for s in request.form.getlist("dest_component"):
        if s in valid_comps: new_dests.append(("component", s))

    # Body coming from a plain-text <textarea> — wrap in <p> if non-empty.
    body_html = f"<p>{body_text}</p>" if body_text else ""

    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    db.execute(
        """UPDATE sub_considerations
              SET consideration_id = ?, one_liner = ?, body = ?,
                  source_url = ?, source_date = ?, status = 'approved',
                  last_updated = ?
            WHERE id = ?""",
        (cons_id, one_liner[:240], body_html, source_url, source_date, now, sub_id),
    )
    db.execute("DELETE FROM sub_consideration_phases WHERE sub_consideration_id = ?", (sub_id,))
    for pos, slug in enumerate(phase_slugs, start=1):
        db.execute(
            "INSERT INTO sub_consideration_phases (sub_consideration_id, phase_slug, position) VALUES (?, ?, ?)",
            (sub_id, slug, pos),
        )
    # Update destinations of the consideration the sub now lives under.
    # Replace-all only when the form actually submitted destinations; an
    # empty submit means "don't touch" — protects against accidental
    # wipes if JS misbehaves or the user clears all by mistake.
    if submitted_dests and new_dests:
        db.execute("DELETE FROM consideration_destinations WHERE consideration_id = ?", (cons_id,))
        for kind, slug in new_dests:
            db.execute(
                "INSERT OR IGNORE INTO consideration_destinations (consideration_id, dest_kind, dest_slug) VALUES (?, ?, ?)",
                (cons_id, kind, slug),
            )
    _sync_fts_row(db, sub_id)
    db.commit()
    return redirect(url_for("admin_queue"))


@app.route("/admin/sources")
def admin_sources():
    db = get_db()
    rows = db.execute(
        """SELECT id, name, type, url, status, last_collected, item_count, created_at
             FROM sources
            ORDER BY status = 'paused', LOWER(name)"""
    ).fetchall()
    sources = [{
        "id": r["id"],
        "name": r["name"],
        "type": r["type"],
        "url": r["url"],
        "status": r["status"],
        "last_collected": r["last_collected"],
        "last_collected_human": _format_relative(r["last_collected"]) if r["last_collected"] else "never",
        "item_count": r["item_count"],
    } for r in rows]
    error = request.args.get("error", "").strip()
    return render_template("admin/sources.html", sources=sources, error=error)


@app.route("/admin/sources", methods=["POST"])
def admin_sources_add():
    name = (request.form.get("name") or "").strip()
    url = (request.form.get("url") or "").strip()
    if not name or not url:
        return redirect(url_for("admin_sources", error="Name and URL are required."))
    if not (url.startswith("http://") or url.startswith("https://")):
        return redirect(url_for("admin_sources", error="URL must start with http:// or https://."))
    db = get_db()
    db.execute(
        """INSERT INTO sources (name, type, url, status, created_at)
           VALUES (?, 'rss', ?, 'active', ?)""",
        (name, url, datetime.now(timezone.utc).isoformat(timespec="seconds")),
    )
    db.commit()
    return redirect(url_for("admin_sources"))


@app.route("/admin/sources/<int:source_id>/toggle", methods=["POST"])
def admin_sources_toggle(source_id):
    db = get_db()
    row = db.execute("SELECT status FROM sources WHERE id = ?", (source_id,)).fetchone()
    if not row:
        abort(404)
    # Error → active (operator unblocking the feed); active ↔ paused otherwise.
    new_status = "active" if row["status"] in ("paused", "error") else "paused"
    db.execute("UPDATE sources SET status = ? WHERE id = ?", (new_status, source_id))
    db.commit()
    return redirect(url_for("admin_sources"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5681, debug=False)
