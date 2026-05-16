"""bestpractice — RSS ingestion. Walks active sources, fetches with
RFC 7232 conditional GET, dedups against existing sub_considerations
URLs, and inserts new candidates as pending rows under the ingest
inbox consideration. Designed to be re-run safely on any interval.

Adapted from E:/_dev/musemaniac/scripts/collect_news.py: the
conditional-GET pattern (If-None-Match / If-Modified-Since → 304) and
the feedparser entry shape. Storage differs — etag/last_modified live
on sources rows instead of a sidecar JSON cache, and dedup is by
source_url rather than a content_hash table.

Usage: python collect.py
"""
from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("BESTPRACTICE_DB", str(ROOT / "data" / "bestpractice.db")))

USER_AGENT = "bestpractice-collector/0.1 (+https://best.amusealot.com)"
REQUEST_TIMEOUT = 30
BODY_MAX_CHARS = 600
ACCEPTED_LANGS = {"", "en", "en-us", "en-gb", "en_us", "en_gb"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def strip_html_to_text(html: str) -> str:
    """Cheap HTML→text: drop tags, collapse whitespace."""
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def first_paragraph_body(html_or_text: str) -> str:
    """Reduce an entry's summary/content to a single capped paragraph
    wrapped in <p>. Echoes the Session 7 lesson: structural tags in
    fixture/body content are a foot-gun — keep ingestion plain-text
    only, let the editor add inline formatting via edit-and-approve.
    """
    text = strip_html_to_text(html_or_text)
    if len(text) > BODY_MAX_CHARS:
        text = text[:BODY_MAX_CHARS].rsplit(" ", 1)[0].rstrip(",.;:—-") + "…"
    if not text:
        return ""
    # Escape any remaining < / > / & defensively.
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"<p>{text}</p>"


def parsed_struct_to_iso(struct) -> str | None:
    """feedparser time.struct_time → ISO 8601 Z."""
    if not struct:
        return None
    try:
        dt = datetime(*struct[:6], tzinfo=timezone.utc)
        return dt.isoformat(timespec="seconds").replace("+00:00", "Z")
    except (TypeError, ValueError):
        return None


def get_inbox_id(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT id FROM considerations WHERE parent_type='page_type' AND parent_slug='site-wide' AND slug='ingest-inbox'"
    ).fetchone()
    if not row:
        print("ERROR: ingest-inbox consideration missing. Run python init_db.py.", file=sys.stderr)
        sys.exit(2)
    return row[0]


def existing_urls(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute(
        "SELECT source_url FROM sub_considerations WHERE source_url <> ''"
    ).fetchall()}


def fetch_with_conditional_get(url: str, etag: str | None, last_modified: str | None):
    """Issue a conditional GET. Returns (response, was_304). On 304,
    response.text is irrelevant — feed unchanged."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*"}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    return response, response.status_code == 304


def slug_from_url(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]


def collect_one_source(conn: sqlite3.Connection, source: sqlite3.Row, inbox_id: int, known_urls: set[str]) -> tuple[int, int]:
    """Returns (inserted, skipped_existing). Updates the source row on success.
    On exception flips status='error' and re-raises so the caller can count."""
    src_id = source["id"]
    name = source["name"]
    url = source["url"]
    print(f"\n[{name}] {url}")
    try:
        response, not_modified = fetch_with_conditional_get(url, source["etag"], source["last_modified"])
        if not_modified:
            print("  304 not modified")
            conn.execute(
                "UPDATE sources SET last_fetched = ? WHERE id = ?",
                (now_iso(), src_id),
            )
            conn.commit()
            return 0, 0
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"  fetch error: {exc}")
        conn.execute(
            "UPDATE sources SET status = 'error', last_fetched = ? WHERE id = ?",
            (now_iso(), src_id),
        )
        conn.commit()
        return 0, 0

    if not response.encoding or response.encoding.lower() == "iso-8859-1":
        response.encoding = "utf-8"

    feed = feedparser.parse(response.text)
    if feed.bozo and not feed.entries:
        print(f"  parse error: {feed.get('bozo_exception')!r}")
        conn.execute(
            "UPDATE sources SET status = 'error', last_fetched = ? WHERE id = ?",
            (now_iso(), src_id),
        )
        conn.commit()
        return 0, 0

    print(f"  {len(feed.entries)} entries")

    inserted = 0
    skipped = 0
    now = now_iso()
    for entry in feed.entries:
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not title or not link:
            continue

        lang = (entry.get("language") or feed.feed.get("language") or "").strip().lower()
        if lang and lang not in ACCEPTED_LANGS:
            continue

        if link in known_urls:
            skipped += 1
            continue

        published = (
            parsed_struct_to_iso(entry.get("published_parsed"))
            or parsed_struct_to_iso(entry.get("updated_parsed"))
        )
        source_date = published[:10] if published else now[:10]

        body_html = ""
        if entry.get("content"):
            try:
                body_html = entry.content[0].get("value", "")
            except (IndexError, AttributeError):
                body_html = ""
        if not body_html:
            body_html = entry.get("summary") or entry.get("description") or ""

        body = first_paragraph_body(body_html)

        slug = slug_from_url(link)
        try:
            conn.execute(
                """INSERT INTO sub_considerations
                       (consideration_id, slug, one_liner, body,
                        source_name, source_title, source_url, source_date,
                        status, display_order, created_at, last_updated)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', 0, ?, ?)""",
                (inbox_id, slug, title[:280], body, name, title, link, source_date, now, now),
            )
            inserted += 1
            known_urls.add(link)
        except sqlite3.IntegrityError as exc:
            # UNIQUE (consideration_id, slug) collision — same URL hash, treat as dup.
            print(f"  dup slug for {link}: {exc}")
            skipped += 1

    new_etag = response.headers.get("ETag")
    new_last_modified = response.headers.get("Last-Modified")
    conn.execute(
        """UPDATE sources
              SET status='active',
                  last_collected = ?,
                  last_fetched = ?,
                  etag = COALESCE(?, etag),
                  last_modified = COALESCE(?, last_modified),
                  item_count = item_count + ?
            WHERE id = ?""",
        (now, now, new_etag, new_last_modified, inserted, src_id),
    )
    conn.commit()
    print(f"  inserted {inserted}, skipped {skipped} (existing)")
    return inserted, skipped


def main() -> int:
    if not DB_PATH.exists():
        print(f"ERROR: DB missing at {DB_PATH}. Run python init_db.py.", file=sys.stderr)
        return 2

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    inbox_id = get_inbox_id(conn)
    known_urls = existing_urls(conn)
    print(f"db: {DB_PATH}")
    print(f"inbox consideration id: {inbox_id}")
    print(f"known URLs: {len(known_urls)}")

    sources = conn.execute(
        """SELECT id, name, url, etag, last_modified
             FROM sources
            WHERE type='rss' AND status IN ('active','error')
            ORDER BY name"""
    ).fetchall()
    print(f"sources to fetch: {len(sources)}")

    totals_inserted = 0
    totals_skipped = 0
    errors = 0
    for source in sources:
        try:
            ins, skip = collect_one_source(conn, source, inbox_id, known_urls)
            totals_inserted += ins
            totals_skipped += skip
        except Exception as exc:  # noqa: BLE001
            errors += 1
            print(f"  unexpected error: {exc}")
        time.sleep(0.5)  # be polite

    print(f"\ntotals: inserted={totals_inserted} skipped={totals_skipped} errors={errors}")
    conn.close()
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
