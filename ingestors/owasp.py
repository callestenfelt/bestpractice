"""OWASP Top 10 (2021) adapter.

Source: github.com/OWASP/Top10 — markdown sources under 2021/docs/en/.
Ten A0N files (A01–A10) each describing one risk category. We pull the
H1 + "Description" section of each.

Slow source. Top 10 releases are years apart. Re-fetch monthly is
plenty. URL dedup on the per-category page works for re-runs.

For v1 we only ingest the 10 categories. The OWASP Cheat Sheet Series
(github.com/OWASP/CheatSheetSeries — ~100 cheat sheets) is much larger
and stays parked for a future adapter or a capped second pass.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import requests

SOURCE_NAME = "OWASP Top 10"
FEED_URL = "https://raw.githubusercontent.com/OWASP/Top10/master/2021/docs/en/"
CACHE_FILENAME = "owasp_top10.json"  # we cache the rendered candidates
OWASP_2021_DATE = "2021-09-24"  # OWASP Top 10:2021 release

_USER_AGENT = "bestpractice-collector/0.1 (+https://best.amusealot.com)"
_BODY_MAX_CHARS = 1500

_FILES = [
    ("A01", "A01_2021-Broken_Access_Control.md"),
    ("A02", "A02_2021-Cryptographic_Failures.md"),
    ("A03", "A03_2021-Injection.md"),
    ("A04", "A04_2021-Insecure_Design.md"),
    ("A05", "A05_2021-Security_Misconfiguration.md"),
    ("A06", "A06_2021-Vulnerable_and_Outdated_Components.md"),
    ("A07", "A07_2021-Identification_and_Authentication_Failures.md"),
    ("A08", "A08_2021-Software_and_Data_Integrity_Failures.md"),
    ("A09", "A09_2021-Security_Logging_and_Monitoring_Failures.md"),
    ("A10", "A10_2021-Server-Side_Request_Forgery_%28SSRF%29.md"),
]


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _extract_description(markdown: str) -> str:
    """Return the prose under the first '## Description' header, stripped
    of markdown bullets / links to plain text."""
    match = re.search(r"^##\s+Description\s*\n(.*?)(?=^##\s|\Z)", markdown, re.M | re.S)
    if not match:
        return ""
    body = match.group(1)
    # Drop list markers and stray indentation.
    body = re.sub(r"^[\s-]*\*\s*", "", body, flags=re.M)
    body = re.sub(r"^-\s+", "• ", body, flags=re.M)
    # Strip link markdown: [text](url) → text
    body = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body)
    # Strip emphasis markers / inline code backticks
    body = re.sub(r"[*_`]", "", body)
    body = re.sub(r"\s+", " ", body).strip()
    return body


def _extract_h1(markdown: str) -> str:
    match = re.match(r"^#\s+(.+?)(?:\s*!\[|\s*$)", markdown, re.M)
    if not match:
        return ""
    return match.group(1).strip()


def fetch_candidates(conn: sqlite3.Connection, source_row, max_new: int | None = None) -> list[dict]:
    existing_urls = {r[0] for r in conn.execute(
        "SELECT source_url FROM sub_considerations WHERE source_url LIKE 'https://owasp.org/Top10/%'"
    ).fetchall()}

    headers = {"User-Agent": _USER_AGENT, "Accept": "text/plain"}
    candidates: list[dict] = []

    for code, filename in _FILES:
        url_canonical = f"https://owasp.org/Top10/{filename.replace('.md', '/').replace('A0', 'A0').replace('%28SSRF%29', '%28SSRF%29')}"
        # owasp.org URLs drop the .md and use the underscored slug as a directory.
        slug_dir = filename.replace(".md", "").replace("%28", "(").replace("%29", ")")
        url_canonical = f"https://owasp.org/Top10/{slug_dir}/"

        if url_canonical in existing_urls:
            continue

        fetch_url = FEED_URL + filename
        try:
            resp = requests.get(fetch_url, headers=headers, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"  {code}: fetch error {exc}")
            continue
        markdown = resp.text
        h1 = _extract_h1(markdown) or f"{code}:2021"
        description = _extract_description(markdown) or ""
        if not description:
            print(f"  {code}: no Description section found")
            continue

        body_text = description
        if len(body_text) > _BODY_MAX_CHARS:
            body_text = body_text[:_BODY_MAX_CHARS].rsplit(" ", 1)[0].rstrip(",.;:—-") + "…"

        one_liner = f"OWASP {h1}"
        if len(one_liner) > 240:
            one_liner = one_liner[:237] + "…"

        candidates.append({
            "slug": f"owasp-2021-{code.lower()}",
            "one_liner": one_liner,
            "body": f"<p>{_escape(body_text)}</p>",
            "source_name": SOURCE_NAME,
            "source_url": url_canonical,
            "source_title": f"OWASP {h1}",
            "source_date": OWASP_2021_DATE,
        })
        if max_new and len(candidates) >= max_new:
            break
    return candidates
