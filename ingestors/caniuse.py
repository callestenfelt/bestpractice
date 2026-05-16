"""caniuse.com adapter — browser-support data for web platform features.

Source: raw.githubusercontent.com/Fyrd/caniuse/main/data.json (~4.5 MB,
554 features as of 2026). Each feature becomes a sub_consideration with
the feature's description as body and the source spec URL.

Quality filter: only ingest features with status in ('ls','rec','pr','wd')
(living standards, W3C recommendations, proposed, working drafts) — skip
'other' and 'unoff' which include legacy / non-standard items.

First-run cap (MAX_NEW_PER_RUN, default 25) keeps the queue manageable;
subsequent runs continue from where the previous run stopped (URL dedup
handles already-ingested features automatically).
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import requests

SOURCE_NAME = "caniuse"
FEED_URL = "https://raw.githubusercontent.com/Fyrd/caniuse/main/data.json"
CACHE_FILENAME = "caniuse.json"

_USER_AGENT = "bestpractice-collector/0.1 (+https://best.amusealot.com)"
_BODY_MAX_CHARS = 1000
_GOOD_STATUSES = {"ls", "rec", "pr", "wd"}
# Categories we want to surface; skip super-niche / legacy buckets.
_GOOD_CATEGORIES = {
    "CSS", "CSS2", "CSS3",
    "HTML5", "DOM",
    "JS", "JS API",
    "Security", "Canvas", "SVG",
    "Other",  # caniuse uses 'Other' for a chunk of useful modern features (e.g. dialog)
}
_STATUS_LABELS = {
    "ls": "Living Standard",
    "rec": "W3C Recommendation",
    "pr": "Proposed Recommendation",
    "wd": "Working Draft",
}


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _support_summary(feat: dict) -> str:
    """One short line summarizing supported browsers (e.g. 'Wide support
    in Chrome, Firefox, Safari, Edge')."""
    stats = feat.get("stats") or {}
    supported: list[str] = []
    for browser in ("chrome", "firefox", "safari", "edge"):
        versions = stats.get(browser) or {}
        # 'y' = full support in some recent version. Walk versions in
        # caniuse order and see if any modern version has 'y'.
        if any(v == "y" or (isinstance(v, str) and v.startswith("y ")) for v in versions.values()):
            supported.append({"chrome": "Chrome", "firefox": "Firefox",
                              "safari": "Safari", "edge": "Edge"}[browser])
    if len(supported) == 4:
        return "Supported in all major browsers."
    if supported:
        return f"Supported in: {', '.join(supported)}."
    return "Limited / partial browser support."


def fetch_candidates(conn: sqlite3.Connection, source_row, max_new: int | None = None) -> list[dict]:
    cap = max_new if max_new is not None else 25

    cache_dir = Path("data/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / CACHE_FILENAME

    headers = {"User-Agent": _USER_AGENT, "Accept": "application/json"}
    if source_row["etag"]:
        headers["If-None-Match"] = source_row["etag"]
    if source_row["last_modified"]:
        headers["If-Modified-Since"] = source_row["last_modified"]

    resp = requests.get(FEED_URL, headers=headers, timeout=45)
    if resp.status_code == 304:
        print("  304 not modified")
        return []
    resp.raise_for_status()
    data = resp.json()
    cache_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    conn.execute(
        "UPDATE sources SET etag = COALESCE(?, etag), last_modified = COALESCE(?, last_modified) WHERE id = ?",
        (resp.headers.get("ETag"), resp.headers.get("Last-Modified"), source_row["id"]),
    )

    existing_urls = {r[0] for r in conn.execute(
        "SELECT source_url FROM sub_considerations WHERE source_url LIKE 'https://caniuse.com/%'"
    ).fetchall()}

    feats = data.get("data") or {}
    updated_iso = data.get("updated")
    # caniuse's `updated` is a unix timestamp; convert to ISO date for source_date.
    source_date = None
    if isinstance(updated_iso, int):
        from datetime import datetime, timezone
        source_date = datetime.fromtimestamp(updated_iso, timezone.utc).date().isoformat()

    candidates: list[dict] = []
    for feat_id, feat in feats.items():
        if not isinstance(feat, dict):
            continue
        status = feat.get("status")
        if status not in _GOOD_STATUSES:
            continue
        categories = feat.get("categories") or []
        if not any(c in _GOOD_CATEGORIES for c in categories):
            continue
        title = (feat.get("title") or "").strip()
        description = _strip_html(feat.get("description") or "")
        if not title or not description:
            continue
        url = f"https://caniuse.com/{feat_id}"
        if url in existing_urls:
            continue

        status_label = _STATUS_LABELS.get(status, status)
        category_label = next((c for c in categories if c in _GOOD_CATEGORIES), categories[0] if categories else "")
        one_liner = f"{title} ({status_label})"
        if len(one_liner) > 240:
            one_liner = one_liner[:237] + "…"

        body_parts = [description, _support_summary(feat)]
        body_text = " ".join(body_parts)
        if len(body_text) > _BODY_MAX_CHARS:
            body_text = body_text[:_BODY_MAX_CHARS].rsplit(" ", 1)[0].rstrip(",.;:—-") + "…"
        body = f"<p>{_escape(body_text)}</p>"

        candidates.append({
            "slug": f"caniuse-{feat_id}",
            "one_liner": one_liner,
            "body": body,
            "source_name": SOURCE_NAME,
            "source_url": url,
            "source_title": f"caniuse · {title}",
            "source_date": source_date or "",
        })
        if len(candidates) >= cap:
            break

    return candidates
