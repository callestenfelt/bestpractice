"""bestpractice — Groq scoring pass. Iterates pending sub_considerations
that have no relevance_score yet, runs each through Llama 3.3 to produce
(score, phases, suggested consideration_id, rewritten one_liner, edited
body), and writes the result back. PROJECT.md §6.1 is the spec.

Auto-reject threshold: score < 4 flips status='rejected'. Items where
the AI returns malformed output are left untouched so the next run can
retry.

Reference: E:/_dev/musemaniac/scripts/score_news.py — same Groq HTTP
shape (raw requests, response_format=json_object, exponential backoff
on 429), different prompt + storage.

Usage: python score.py [--limit N] [--threshold X]
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

import requests
from dotenv import load_dotenv

# Windows consoles default to cp1252; force utf-8 so non-ASCII characters
# in log lines (and AI output) don't crash mid-run.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

load_dotenv()

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("BESTPRACTICE_DB", str(ROOT / "data" / "bestpractice.db")))

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

DELAY_BETWEEN_CALLS = 2.0
REQUEST_TIMEOUT = 60
MAX_RETRIES = 3

REJECT_THRESHOLD = 4  # PROJECT.md §6.1 starting threshold

# Session 14: kinds the editorial tool actually wants. Anything else auto-rejects
# regardless of score — a feature-release blog post can be technically strong
# (score 8) and still not belong here.
KEEP_KINDS = {"guidance", "reference"}
VALID_KINDS = KEEP_KINDS | {"news", "discussion", "tutorial", "case-study", "marketing", "other"}

# Session 14b: cap on multi-placement suggestions per item. Anything beyond
# ~4 destinations is usually the model padding to look thorough; the editor
# can add more manually if a topic genuinely cross-cuts.
MAX_PLACEMENTS = 4

SYSTEM_PROMPT = """You score and route items for "bestpractice", a personal reference tool of web/UX best practices used by one senior product professional. The audience is experienced: a working UX/frontend lead, not a beginner.

Be selective. Most items will be tier 3 (skip). Promote only what is specific, actionable, and grounded in primary sources (specs, WCAG, web platform docs, original research). Penalise marketing, vague opinion, recycled commentary, listicles, and beginner explainers.

Classify each item by kind BEFORE scoring. Only "guidance" and "reference" belong in this tool. A new spec/feature/release is "news", not "guidance", even if technically substantive — the user wants the rule, not the announcement. A tutorial that teaches an existing tool is "tutorial", not "guidance". An opinion or commentary piece is "discussion". When in doubt between "guidance" and "news"/"tutorial"/"discussion", prefer the latter.

For each item, return a JSON object with EXACTLY these fields:

- "kind": one of "guidance", "reference", "news", "discussion", "tutorial",
  "case-study", "marketing", "other". Items not "guidance" or "reference"
  will be auto-rejected regardless of score.
    guidance   = enduring rule, principle, or checklist item
    reference  = primary-source spec / standard / WCAG SC / API doc
    news       = announcement, release post, "X is now in Chrome", roadmap
    discussion = opinion, commentary, "thoughts on…", debate
    tutorial   = step-by-step walkthrough, "how to set up X"
    case-study = single-project retrospective
    marketing  = vendor pitch, product page
    other      = doesn't fit above

- "score": integer 1-10
    10 = essential primary-source guidance (e.g. a new WCAG SC, a spec milestone)
    7-9 = strong, specific, technically substantive
    4-6 = relevant but secondary or partial
    1-3 = off-topic, fluff, marketing, or beginner content (will be auto-rejected)

- "phases": array of 1-3 phase slugs from this list — pick the disciplines
  where someone working on this item would actually do the work. Empty
  array is reserved for the rare item that genuinely cuts across every
  phase equally (e.g. a foundational principle); most items have a
  primary discipline angle, so prefer 1-2 over zero. Do not invent slugs.
  strategy, concept, ux, design, frontend, backend, content, seo,
  measurement, maintenance, legal

- "placements": array of 0-4 consideration ids from the list provided in
  the user message. REASON ABOUT SCOPE BEFORE PICKING IDS:
    1. What page feature does this guidance apply to? (URL, page title,
       headings, form, header, primary CTA, transactional flow, content
       body, list/index, structured data, performance, …)
    2. Is that feature universal (every page), categorical (a subset of
       pages share the feature), or specific (one page-type/component)?
    3. Pick from the catalog accordingly:
       - Universal → the [SITE-WIDE] consideration. NEVER enumerate
         page-types for guidance that obviously applies everywhere. If
         the rule is about URLs, page titles, meta descriptions,
         heading hierarchy, Core Web Vitals, security, privacy,
         accessibility, performance, measurement, or internationalization,
         it belongs on the matching [SITE-WIDE] consideration. Listing
         five page-types here is wrong.
       - Categorical → the [CAT:<slug>] consideration. The cheat-sheet
         at the bottom of this message lists each category's members.
         Form-validation guidance belongs on [CAT:has-form], not on
         auth-page + checkout-page + contact-page.
       - Specific → the page-type or component consideration. Reserve
         these for guidance whose angle is tied to that surface
         (e.g. "Article H1 should match the byline angle" → article-page;
         "Cookie banner accept/decline parity" → cookie-banner component).
  Cap at 4. Most items want 1-2; reach for 3-4 only when the guidance
  genuinely needs both a universal/categorical placement AND a specific
  one (e.g. a form rule that has a special twist for checkout). Empty
  list is fine — better than a forced fit.

- "one_liner": rewritten one-line summary, ≤ 120 characters, terse,
  no marketing language, no emoji. Make it scannable and specific.

- "body": ONE short paragraph (2-4 sentences) capturing the substance.
  Plain text only — no <p> wrapper, no other HTML tags. Cite the source
  by name once if natural; do not invent facts beyond the input.

Tone: terse, factual, no hedging, no "Discover how…" / "In this article…"
openings. Bias toward primary sources over commentary."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def fetch_pending(conn: sqlite3.Connection, limit: int | None, rescore: bool = False) -> list[sqlite3.Row]:
    # Default mode picks up un-scored pending rows only (normal post-collect run).
    # --rescore drops the relevance_score filter so the existing pending queue
    # gets re-classified one-shot; safe to interrupt because each apply_result
    # commits per row and rejected rows fall out of subsequent pending selects.
    where = "status='pending'" if rescore else "status='pending' AND relevance_score IS NULL"
    sql = f"""SELECT id, slug, one_liner, body, source_name, source_url,
                     source_title, source_date
                FROM sub_considerations
               WHERE {where}
               ORDER BY id"""
    if limit:
        sql += f" LIMIT {int(limit)}"
    return conn.execute(sql).fetchall()


def fetch_consideration_catalog(conn: sqlite3.Connection) -> tuple[list[dict], set[int]]:
    """Returns ([{id, label}], {valid_ids}). Skips the ingest-inbox row;
    items shouldn't be routed back to it.

    Label encoding tags each cons with its destination class so Groq can
    reason about scope:
      [SITE-WIDE]    — applies to every page (URL hygiene, page titles, etc.)
      [CAT:<slug>]   — applies to every page in the category (e.g. has-form)
      <Parent Label> — a specific page-type or component
    A cons with multiple destinations gets the most-fanned-out prefix.
    """
    cons_rows = conn.execute(
        """SELECT c.id, c.title, c.group_label
             FROM considerations c
            WHERE c.status='approved' AND c.slug != 'ingest-inbox'
            ORDER BY c.group_order, c.display_order, c.id"""
    ).fetchall()
    if not cons_rows:
        return [], set()

    page_type_labels = {r["slug"]: r["label"] for r in conn.execute(
        "SELECT slug, label FROM page_types"
    ).fetchall()}
    component_labels = {r["slug"]: r["label"] for r in conn.execute(
        "SELECT slug, label FROM components"
    ).fetchall()}

    dests_by_cons: dict[int, list[tuple[str, str]]] = {}
    for r in conn.execute(
        "SELECT consideration_id, dest_kind, dest_slug FROM consideration_destinations"
    ).fetchall():
        dests_by_cons.setdefault(r["consideration_id"], []).append(
            (r["dest_kind"], r["dest_slug"])
        )

    def prefix(cons_id: int) -> str:
        dests = dests_by_cons.get(cons_id, [])
        if any(k == "page_type" and s == "site-wide" for k, s in dests):
            return "[SITE-WIDE]"
        cat_dests = [s for k, s in dests if k == "category"]
        if cat_dests:
            return f"[CAT:{cat_dests[0]}]"
        for k, s in dests:
            if k == "page_type":
                return page_type_labels.get(s, s)
            if k == "component":
                return component_labels.get(s, s) + " (component)"
        return "[ORPHAN]"

    catalog = []
    valid_ids = set()
    for r in cons_rows:
        pref = prefix(r["id"])
        if r["group_label"]:
            label = f"{pref} · {r['group_label']} → {r['title']}"
        else:
            label = f"{pref} → {r['title']}"
        catalog.append({"id": r["id"], "label": label})
        valid_ids.add(r["id"])
    return catalog, valid_ids


def fetch_category_summary(conn: sqlite3.Connection) -> list[dict]:
    """Returns [{slug, label, members}] for the feature-presence cheat-sheet
    appended to each scoring prompt. Members is a comma-joined string of
    member page-type slugs."""
    cats = conn.execute(
        """SELECT slug, label, definition FROM page_type_categories
            ORDER BY display_order"""
    ).fetchall()
    members: dict[str, list[str]] = {}
    for r in conn.execute(
        """SELECT category_slug, page_type_slug FROM page_type_in_category"""
    ).fetchall():
        members.setdefault(r["category_slug"], []).append(r["page_type_slug"])
    return [
        {
            "slug": c["slug"],
            "label": c["label"],
            "definition": c["definition"],
            "members": ", ".join(sorted(members.get(c["slug"], []))),
        }
        for c in cats
    ]


def fetch_valid_phases(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute("SELECT slug FROM phases").fetchall()}


def build_user_prompt(item: sqlite3.Row, catalog: list[dict], categories: list[dict]) -> str:
    catalog_lines = "\n".join(f"  [{c['id']}] {c['label']}" for c in catalog)
    body_text = (item["body"] or "").replace("<p>", "").replace("</p>", "")
    cat_lines = "\n".join(
        f"  [CAT:{c['slug']}] {c['label']} — members: {c['members']}"
        for c in categories
    )
    return f"""ITEM:
Source: {item['source_name']}
Source title: {item['source_title']}
URL: {item['source_url']}
Published: {item['source_date']}

Source text:
{body_text}

AVAILABLE CONSIDERATIONS (id → destination):
{catalog_lines}

CATEGORY CHEAT-SHEET (which page-types belong to each [CAT:*]):
{cat_lines}

Pick placements by reasoning about page-feature scope first (see system
prompt). Use [SITE-WIDE] for universal rules, [CAT:*] for categorical
ones, specific page-types/components only when the angle is tied to
that surface. Return one JSON object as specified."""


def groq_call(messages: list[dict]) -> tuple[dict | None, str | None]:
    body = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 800,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(GROQ_URL, headers=headers, json=body, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 429:
                wait = (attempt + 1) * 8
                print(f"    429 rate-limited, sleeping {wait}s")
                time.sleep(wait)
                continue
            if resp.status_code >= 500:
                wait = (attempt + 1) * 4
                print(f"    {resp.status_code}, sleeping {wait}s")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content), None
        except json.JSONDecodeError as exc:
            return None, f"JSON parse: {exc}"
        except requests.RequestException as exc:
            if attempt == MAX_RETRIES - 1:
                return None, f"request: {exc}"
    return None, "max retries exceeded"


def validate_result(result: dict, valid_consideration_ids: set[int], valid_phases: set[str]) -> tuple[dict | None, str | None]:
    try:
        score = int(result.get("score"))
    except (TypeError, ValueError):
        return None, "score not an int"
    if not 1 <= score <= 10:
        return None, f"score out of range: {score}"
    phases = result.get("phases") or []
    if not isinstance(phases, list):
        return None, "phases not a list"
    phases = [p for p in phases if isinstance(p, str) and p in valid_phases]
    # Multi-placement output (Session 14b). Dedupe while preserving order,
    # filter to valid ids, cap at MAX_PLACEMENTS. Empty list is valid and
    # means "leave attached to inbox; user picks placements manually".
    raw_placements = result.get("placements")
    if raw_placements is None:
        # Backward-compat with the old single-pointer field — if the model
        # falls back to it, wrap as a one-element list.
        legacy = result.get("consideration_id")
        raw_placements = [legacy] if legacy is not None else []
    if not isinstance(raw_placements, list):
        return None, "placements not a list"
    placements: list[int] = []
    seen: set[int] = set()
    for p in raw_placements:
        try:
            pid = int(p)
        except (TypeError, ValueError):
            continue
        if pid in valid_consideration_ids and pid not in seen:
            placements.append(pid)
            seen.add(pid)
        if len(placements) >= MAX_PLACEMENTS:
            break
    one_liner = (result.get("one_liner") or "").strip()
    if not one_liner:
        return None, "one_liner empty"
    if len(one_liner) > 240:
        one_liner = one_liner[:240]
    body = (result.get("body") or "").strip()
    # Strip any HTML the model may have leaked despite the instruction.
    body = body.replace("<p>", "").replace("</p>", "")
    # Default missing/unknown kinds to "other" rather than failing the row —
    # rejection is reversible; the editor can re-queue from the Rejected bin.
    kind = (result.get("kind") or "other").strip().lower()
    if kind not in VALID_KINDS:
        kind = "other"
    return {
        "score": score,
        "kind": kind,
        "phases": phases,
        "placements": placements,
        "one_liner": one_liner,
        "body": f"<p>{body}</p>" if body else "",
    }, None


def apply_result(conn: sqlite3.Connection, item_id: int, parsed: dict, threshold: int) -> str:
    """Write scoring result. Returns the new status."""
    now = now_iso()
    reject_for_kind = parsed["kind"] not in KEEP_KINDS
    reject_for_score = parsed["score"] < threshold
    new_status = "rejected" if (reject_for_kind or reject_for_score) else "pending"
    # The legacy consideration_id column stays in sync with the first
    # placement so the queue list's "Suggested home" breadcrumb keeps
    # working. If Groq returns no placements, leave consideration_id
    # untouched — the row stays attached to its current parent (inbox on
    # fresh collect, or the previous placement on rescore).
    placements: list[int] = parsed["placements"]
    primary_cons_id = placements[0] if placements else None
    if primary_cons_id is None:
        conn.execute(
            """UPDATE sub_considerations
                  SET relevance_score = ?, content_kind = ?, one_liner = ?,
                      body = ?, status = ?, last_updated = ?
                WHERE id = ?""",
            (parsed["score"], parsed["kind"], parsed["one_liner"], parsed["body"], new_status, now, item_id),
        )
    else:
        conn.execute(
            """UPDATE sub_considerations
                  SET consideration_id = ?, relevance_score = ?, content_kind = ?,
                      one_liner = ?, body = ?, status = ?, last_updated = ?
                WHERE id = ?""",
            (primary_cons_id, parsed["score"], parsed["kind"], parsed["one_liner"], parsed["body"], new_status, now, item_id),
        )

    # Idempotent placement write: clear and re-insert so rescoring on a
    # row with stale AI picks fully refreshes the destination set.
    conn.execute("DELETE FROM sub_consideration_placements WHERE sub_id = ?", (item_id,))
    for pos, cons_id in enumerate(placements, start=1):
        conn.execute(
            "INSERT INTO sub_consideration_placements (sub_id, consideration_id, position) VALUES (?, ?, ?)",
            (item_id, cons_id, pos),
        )

    conn.execute("DELETE FROM sub_consideration_phases WHERE sub_consideration_id = ?", (item_id,))
    for pos, phase_slug in enumerate(parsed["phases"], start=1):
        conn.execute(
            "INSERT INTO sub_consideration_phases (sub_consideration_id, phase_slug, position) VALUES (?, ?, ?)",
            (item_id, phase_slug, pos),
        )
    conn.commit()
    return new_status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Cap rows scored this run")
    parser.add_argument("--threshold", type=int, default=REJECT_THRESHOLD, help="Auto-reject below this score")
    parser.add_argument("--rescore", action="store_true",
        help="Re-score every status='pending' row (ignores existing relevance_score). One-shot cleanup of the current queue.")
    args = parser.parse_args()

    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY missing from env. Set it in .env.", file=sys.stderr)
        return 2
    if not DB_PATH.exists():
        print(f"ERROR: DB missing at {DB_PATH}. Run python init_db.py.", file=sys.stderr)
        return 2

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    pending = fetch_pending(conn, args.limit, rescore=args.rescore)
    catalog, valid_cons_ids = fetch_consideration_catalog(conn)
    categories = fetch_category_summary(conn)
    valid_phases = fetch_valid_phases(conn)

    print(f"db: {DB_PATH}")
    print(f"model: {GROQ_MODEL}")
    print(f"mode: {'rescore-all-pending' if args.rescore else 'score-unscored'}")
    print(f"pending to score: {len(pending)}")
    print(f"consideration catalog: {len(catalog)}")
    print(f"reject threshold: < {args.threshold}\n")

    approved = 0
    rejected = 0
    errors = 0

    for idx, item in enumerate(pending, start=1):
        prompt = build_user_prompt(item, catalog, categories)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        result, err = groq_call(messages)
        if err or result is None:
            print(f"[{idx}/{len(pending)}] #{item['id']} ERROR: {err}")
            errors += 1
            time.sleep(DELAY_BETWEEN_CALLS)
            continue

        parsed, verr = validate_result(result, valid_cons_ids, valid_phases)
        if verr or parsed is None:
            print(f"[{idx}/{len(pending)}] #{item['id']} INVALID: {verr}")
            errors += 1
            time.sleep(DELAY_BETWEEN_CALLS)
            continue

        status = apply_result(conn, item["id"], parsed, args.threshold)
        if status == "rejected":
            rejected += 1
        else:
            approved += 1
        phases_short = ",".join(parsed["phases"]) or "-"
        placements_short = ",".join(str(p) for p in parsed["placements"]) or "inbox"
        print(f"[{idx}/{len(pending)}] #{item['id']} score={parsed['score']} kind={parsed['kind']} phases={phases_short} → [{placements_short}] [{status}]")

        time.sleep(DELAY_BETWEEN_CALLS)

    print(f"\ntotals: scored_pending={approved} rejected={rejected} errors={errors}")
    conn.close()
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
