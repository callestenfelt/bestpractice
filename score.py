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

SYSTEM_PROMPT = """You score and route items for "bestpractice", a personal reference tool of web/UX best practices used by one senior product professional. The audience is experienced: a working UX/frontend lead, not a beginner.

Be selective. Most items will be tier 3 (skip). Promote only what is specific, actionable, and grounded in primary sources (specs, WCAG, web platform docs, original research). Penalise marketing, vague opinion, recycled commentary, listicles, and beginner explainers.

For each item, return a JSON object with EXACTLY these fields:

- "score": integer 1-10
    10 = essential primary-source guidance (e.g. a new WCAG SC, a spec milestone)
    7-9 = strong, specific, technically substantive
    4-6 = relevant but secondary or partial
    1-3 = off-topic, fluff, marketing, or beginner content (will be auto-rejected)

- "phases": array of 0+ phase slugs from this list (zero is valid and means
  "applies to all phases"; do not invent slugs):
  strategy, concept, ux, design, frontend, backend, content, seo,
  measurement, maintenance, legal

- "consideration_id": integer id of the best-fit consideration from the
  list provided in the user message, OR null if no existing
  consideration is a good home. Pick null rather than forcing a bad fit.

- "one_liner": rewritten one-line summary, ≤ 120 characters, terse,
  no marketing language, no emoji. Make it scannable and specific.

- "body": ONE short paragraph (2-4 sentences) capturing the substance.
  Plain text only — no <p> wrapper, no other HTML tags. Cite the source
  by name once if natural; do not invent facts beyond the input.

Tone: terse, factual, no hedging, no "Discover how…" / "In this article…"
openings. Bias toward primary sources over commentary."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def fetch_pending(conn: sqlite3.Connection, limit: int | None) -> list[sqlite3.Row]:
    sql = """SELECT id, slug, one_liner, body, source_name, source_url,
                    source_title, source_date
               FROM sub_considerations
              WHERE status='pending' AND relevance_score IS NULL
              ORDER BY id"""
    if limit:
        sql += f" LIMIT {int(limit)}"
    return conn.execute(sql).fetchall()


def fetch_consideration_catalog(conn: sqlite3.Connection) -> tuple[list[dict], set[int]]:
    """Returns ([{id, label}], {valid_ids}). Skips the ingest-inbox row;
    items shouldn't be routed back to it."""
    rows = conn.execute(
        """SELECT c.id, c.title, c.parent_type, c.parent_slug, c.group_label,
                  COALESCE(pt.label, cmp.label) AS parent_label
             FROM considerations c
        LEFT JOIN page_types pt ON c.parent_type='page_type' AND pt.slug=c.parent_slug
        LEFT JOIN components cmp ON c.parent_type='component' AND cmp.slug=c.parent_slug
            WHERE c.status='approved' AND c.slug != 'ingest-inbox'
            ORDER BY c.parent_type, c.parent_slug, c.group_order, c.display_order"""
    ).fetchall()
    catalog = []
    valid_ids = set()
    for r in rows:
        label = f"{r['parent_label']} → {r['title']}"
        if r["group_label"]:
            label = f"{r['parent_label']} · {r['group_label']} → {r['title']}"
        catalog.append({"id": r["id"], "label": label})
        valid_ids.add(r["id"])
    return catalog, valid_ids


def fetch_valid_phases(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute("SELECT slug FROM phases").fetchall()}


def build_user_prompt(item: sqlite3.Row, catalog: list[dict]) -> str:
    catalog_lines = "\n".join(f"  [{c['id']}] {c['label']}" for c in catalog)
    body_text = (item["body"] or "").replace("<p>", "").replace("</p>", "")
    return f"""ITEM:
Source: {item['source_name']}
Source title: {item['source_title']}
URL: {item['source_url']}
Published: {item['source_date']}

Source text:
{body_text}

AVAILABLE CONSIDERATIONS (pick the id for the best fit, or null):
{catalog_lines}

Return one JSON object as specified."""


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
    cons_id = result.get("consideration_id")
    if cons_id is not None:
        try:
            cons_id = int(cons_id)
        except (TypeError, ValueError):
            cons_id = None
        if cons_id not in valid_consideration_ids:
            cons_id = None
    one_liner = (result.get("one_liner") or "").strip()
    if not one_liner:
        return None, "one_liner empty"
    if len(one_liner) > 240:
        one_liner = one_liner[:240]
    body = (result.get("body") or "").strip()
    # Strip any HTML the model may have leaked despite the instruction.
    body = body.replace("<p>", "").replace("</p>", "")
    return {
        "score": score,
        "phases": phases,
        "consideration_id": cons_id,
        "one_liner": one_liner,
        "body": f"<p>{body}</p>" if body else "",
    }, None


def apply_result(conn: sqlite3.Connection, item_id: int, parsed: dict, threshold: int) -> str:
    """Write scoring result. Returns the new status."""
    now = now_iso()
    new_status = "rejected" if parsed["score"] < threshold else "pending"
    new_cons_id = parsed["consideration_id"]
    if new_cons_id is None:
        # Leave the row attached to inbox; record the score only.
        conn.execute(
            """UPDATE sub_considerations
                  SET relevance_score = ?, one_liner = ?, body = ?,
                      status = ?, last_updated = ?
                WHERE id = ?""",
            (parsed["score"], parsed["one_liner"], parsed["body"], new_status, now, item_id),
        )
    else:
        conn.execute(
            """UPDATE sub_considerations
                  SET consideration_id = ?, relevance_score = ?,
                      one_liner = ?, body = ?, status = ?, last_updated = ?
                WHERE id = ?""",
            (new_cons_id, parsed["score"], parsed["one_liner"], parsed["body"], new_status, now, item_id),
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

    pending = fetch_pending(conn, args.limit)
    catalog, valid_cons_ids = fetch_consideration_catalog(conn)
    valid_phases = fetch_valid_phases(conn)

    print(f"db: {DB_PATH}")
    print(f"model: {GROQ_MODEL}")
    print(f"pending to score: {len(pending)}")
    print(f"consideration catalog: {len(catalog)}")
    print(f"reject threshold: < {args.threshold}\n")

    approved = 0
    rejected = 0
    errors = 0

    for idx, item in enumerate(pending, start=1):
        prompt = build_user_prompt(item, catalog)
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
        cons_short = parsed["consideration_id"] if parsed["consideration_id"] else "inbox"
        print(f"[{idx}/{len(pending)}] #{item['id']} score={parsed['score']} phases={phases_short} → {cons_short} [{status}]")

        time.sleep(DELAY_BETWEEN_CALLS)

    print(f"\ntotals: scored_pending={approved} rejected={rejected} errors={errors}")
    conn.close()
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
