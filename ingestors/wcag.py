"""WCAG 2.2 success-criteria adapter.

Source: https://www.w3.org/WAI/WCAG22/wcag.json — W3C's published
machine-readable form of WCAG 2.2. Stable schema:

    {
      "principles": [
        {"num": "1", "title": "...", "guidelines": [
          {"num": "1.1", "title": "...", "successcriteria": [
            {"id": "non-text-content", "num": "1.1.1",
             "handle": "Non-text Content", "title": "...",
             "content": "<p>...</p>", "level": "A",
             "versions": ["2.0", "2.1"]}
          ]}
        ]}
      ],
      "terms": [...]
    }

Each Success Criterion → one sub_consideration. WCAG 2.2 was published
2023-10-05 and the set is locked for that version; new SCs only land
in a new WCAG release, so URL-keyed dedup is sufficient (no in-place
content drift).
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import requests

SOURCE_NAME = "W3C WCAG 2.2"
FEED_URL = "https://www.w3.org/WAI/WCAG22/wcag.json"
CACHE_FILENAME = "wcag.json"
WCAG_PUBLICATION_DATE = "2023-10-05"  # WCAG 2.2 W3C Recommendation date

_USER_AGENT = "bestpractice-collector/0.1 (+https://best.amusealot.com)"
_BODY_MAX_CHARS = 1500


def _strip_html(html: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _build_body(sc: dict) -> str:
    """Compose a plain-text body from sc.content + sc.details. Stay under
    BODY_MAX_CHARS; truncate at a word boundary so the trailing fragment
    isn't a half word."""
    pieces: list[str] = []
    content = _strip_html(sc.get("content") or "")
    if content:
        pieces.append(content)
    # details often carries bullet-list expansions (e.g. for 1.1.1)
    for det in sc.get("details") or []:
        if isinstance(det, dict) and det.get("type") == "ulist":
            for item in det.get("items") or []:
                handle = (item.get("handle") or "").strip()
                txt = _strip_html(item.get("text") or "")
                if handle and txt:
                    pieces.append(f"{handle}: {txt}")
                elif txt:
                    pieces.append(txt)
    body = " · ".join(pieces)
    if len(body) > _BODY_MAX_CHARS:
        body = body[:_BODY_MAX_CHARS].rsplit(" ", 1)[0].rstrip(",.;:—-") + "…"
    return f"<p>{_escape(body)}</p>" if body else ""


def fetch_candidates(conn: sqlite3.Connection, source_row, max_new: int | None = None) -> list[dict]:
    cache_dir = Path("data/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / CACHE_FILENAME

    headers = {"User-Agent": _USER_AGENT, "Accept": "application/json"}
    if source_row["etag"]:
        headers["If-None-Match"] = source_row["etag"]
    if source_row["last_modified"]:
        headers["If-Modified-Since"] = source_row["last_modified"]

    resp = requests.get(FEED_URL, headers=headers, timeout=30)
    if resp.status_code == 304:
        print(f"  304 not modified")
        return []
    resp.raise_for_status()

    data = resp.json()
    cache_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Capture conditional-GET state on the source row for the next run.
    conn.execute(
        "UPDATE sources SET etag = COALESCE(?, etag), last_modified = COALESCE(?, last_modified) WHERE id = ?",
        (resp.headers.get("ETag"), resp.headers.get("Last-Modified"), source_row["id"]),
    )

    existing_urls = {r[0] for r in conn.execute(
        "SELECT source_url FROM sub_considerations WHERE source_url LIKE 'https://www.w3.org/TR/WCAG22/%'"
    ).fetchall()}

    candidates: list[dict] = []
    for principle in data.get("principles", []):
        for guideline in principle.get("guidelines", []):
            for sc in guideline.get("successcriteria", []):
                sc_id = sc.get("id")
                num = sc.get("num")
                handle = sc.get("handle") or ""
                title = (sc.get("title") or "").strip()
                level = sc.get("level") or ""
                if not sc_id or not num or not title:
                    continue
                url = f"https://www.w3.org/TR/WCAG22/#{sc_id}"
                if url in existing_urls:
                    continue
                one_liner = f"WCAG {num} ({level}) — {title[:200]}"
                if len(one_liner) > 240:
                    one_liner = one_liner[:237] + "…"
                candidates.append({
                    "slug": f"wcag22-{num.replace('.', '-')}",
                    "one_liner": one_liner,
                    "body": _build_body(sc),
                    "source_name": SOURCE_NAME,
                    "source_url": url,
                    "source_title": f"WCAG {num} {handle}",
                    "source_date": WCAG_PUBLICATION_DATE,
                })
                if max_new and len(candidates) >= max_new:
                    return candidates
    return candidates
