"""GOV.UK Design System adapter — components + patterns.

Source: github.com/alphagov/govuk-design-system, the source repo (not
the rendered design-system.service.gov.uk site, per PROJECT.md §5.1's
"ingest from the source repo, not the rendered HTML site"). Each
component and pattern lives in its own directory under src/components/
and src/patterns/, with the canonical doc in index.md. We extract the
YAML frontmatter (title, description) and the intro paragraph plus the
"When to use this component" / "When to use this pattern" section.

34 components + 35 patterns = ~69 candidates first run. Slow-moving
source; re-fetch monthly is fine. URL-keyed dedup means re-runs only
emit genuinely-new entries.

The 71 HTTP calls (2 dir listings + 69 raw fetches) take ~30-60 seconds
total at the polite-fetch rate this adapter uses.
"""
from __future__ import annotations

import re
import sqlite3
import time

import requests

SOURCE_NAME = "GOV.UK Design System"
FEED_URL = "https://github.com/alphagov/govuk-design-system"
CACHE_FILENAME = "govuk-design-system.json"

_API_ROOT = "https://api.github.com/repos/alphagov/govuk-design-system/contents"
_RAW_ROOT = "https://raw.githubusercontent.com/alphagov/govuk-design-system/main"
_SITE_ROOT = "https://design-system.service.gov.uk"

_USER_AGENT = "bestpractice-collector/0.1 (+https://best.amusealot.com)"
_BODY_MAX_CHARS = 1500
_PER_FETCH_DELAY = 0.15  # be polite to raw.githubusercontent.com


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _list_dirs(api_path: str) -> list[str]:
    """GET /contents/<path> → list of directory names."""
    headers = {"User-Agent": _USER_AGENT, "Accept": "application/vnd.github+json"}
    resp = requests.get(f"{_API_ROOT}/{api_path}", headers=headers, timeout=20)
    resp.raise_for_status()
    return [e["name"] for e in resp.json() if e.get("type") == "dir"]


def _fetch_index_md(category: str, name: str) -> str | None:
    url = f"{_RAW_ROOT}/src/{category}/{name}/index.md"
    headers = {"User-Agent": _USER_AGENT, "Accept": "text/plain"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.text
    except requests.RequestException:
        pass
    return None


def _parse_frontmatter(md: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). Frontmatter is the YAML block between
    leading '---' fences. Tolerant: missing fences → empty dict + full md."""
    if not md.startswith("---"):
        return {}, md
    end = md.find("\n---", 3)
    if end == -1:
        return {}, md
    block = md[3:end].strip()
    body = md[end + 4:].lstrip("\n")
    fm: dict = {}
    for line in block.splitlines():
        line = line.rstrip()
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            fm[key] = value
    return fm, body


def _strip_nunjucks(md: str) -> str:
    """Drop {% ... %} blocks and {{ ... }} expressions — they're template
    markers, not content. Keep prose intact."""
    md = re.sub(r"\{%[^%]*?%\}", "", md)
    md = re.sub(r"\{\{[^}]*?\}\}", "", md)
    return md


def _extract_body(md: str, title: str) -> str:
    """Compose an ingestion body from the intro paragraph + the first
    'When to use…' section (or first body section, whichever comes first)."""
    md = _strip_nunjucks(md)
    # Drop link markdown: [text](url) → text
    md = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", md)
    # Trim until the first non-empty line.
    md = md.lstrip("\n")

    intro = ""
    section = ""
    parts = re.split(r"(^##\s.*$)", md, flags=re.M)
    if parts:
        intro = parts[0].strip()
        # Strip a leading repeated title line if present (some files start with H1).
        intro = re.sub(r"^#\s+.*\n", "", intro).strip()
        # Find first '## When to use' or fall back to first ## section.
        section_header = ""
        section_body = ""
        for i in range(1, len(parts) - 1, 2):
            header = parts[i].strip()
            body = parts[i + 1].strip()
            if "when to use" in header.lower() or i == 1:
                section_header = header.lstrip("#").strip()
                section_body = body
                if "when to use" in header.lower():
                    break
        if section_body:
            section = f"{section_header}: {section_body}"

    # Strip remaining markdown markers.
    raw = " ".join([intro, section]).strip()
    raw = re.sub(r"[*_`]", "", raw)
    raw = re.sub(r"^-\s+", "• ", raw, flags=re.M)
    raw = re.sub(r"\s+", " ", raw).strip()
    if len(raw) > _BODY_MAX_CHARS:
        raw = raw[:_BODY_MAX_CHARS].rsplit(" ", 1)[0].rstrip(",.;:—-") + "…"
    return f"<p>{_escape(raw)}</p>" if raw else ""


def fetch_candidates(conn: sqlite3.Connection, source_row, max_new: int | None = None) -> list[dict]:
    existing_urls = {r[0] for r in conn.execute(
        "SELECT source_url FROM sub_considerations WHERE source_url LIKE 'https://design-system.service.gov.uk/%'"
    ).fetchall()}

    candidates: list[dict] = []
    for category, label_singular in (("components", "Component"), ("patterns", "Pattern")):
        try:
            names = _list_dirs(f"src/{category}")
        except requests.RequestException as exc:
            print(f"  failed to list {category}: {exc}")
            continue
        for name in names:
            url_canonical = f"{_SITE_ROOT}/{category}/{name}/"
            if url_canonical in existing_urls:
                continue
            md = _fetch_index_md(category, name)
            time.sleep(_PER_FETCH_DELAY)
            if not md:
                continue
            fm, body_md = _parse_frontmatter(md)
            title = fm.get("title") or name.replace("-", " ").title()
            description = fm.get("description") or ""
            one_liner = f"{label_singular}: {title} — {description}" if description else f"{label_singular}: {title}"
            if len(one_liner) > 240:
                one_liner = one_liner[:237] + "…"
            body = _extract_body(body_md, title)
            if not body and description:
                body = f"<p>{_escape(description)}</p>"
            candidates.append({
                "slug": f"govuk-{category}-{name}",
                "one_liner": one_liner,
                "body": body,
                "source_name": SOURCE_NAME,
                "source_url": url_canonical,
                "source_title": f"GOV.UK · {label_singular} · {title}",
                "source_date": "",  # repo doesn't carry per-component dates we can trust
            })
            if max_new and len(candidates) >= max_new:
                return candidates
    return candidates
