"""Schema.org WebPage subtree adapter.

Source: https://schema.org/version/latest/schemaorg-current-https.jsonld —
the full vocabulary as JSON-LD. We extract:

  - Every Type (rdfs:Class) that descends from schema:WebPage in the
    rdfs:subClassOf chain (WebPage itself, AboutPage, ContactPage,
    CheckoutPage, etc.) — these map naturally to bestpractice's
    page-type taxonomy.
  - Every Property whose schema:domainIncludes lists schema:WebPage or
    one of its descendants — these are the structured-data fields
    relevant to the WebPage hierarchy.

3200+ entries in the full graph; the WebPage subtree is ~10 Types and
~30 properties. Stable schema, rarely changes — re-fetch monthly.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import requests

SOURCE_NAME = "Schema.org"
FEED_URL = "https://schema.org/version/latest/schemaorg-current-https.jsonld"
CACHE_FILENAME = "schemaorg.jsonld"
SCHEMA_DATE = "2024-08-22"  # latest version date at time of writing — adapter can be re-pinned

_USER_AGENT = "bestpractice-collector/0.1 (+https://best.amusealot.com)"
_BODY_MAX_CHARS = 1200


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _short_name(at_id: str) -> str:
    """schema:WebPage → WebPage."""
    return at_id.split(":", 1)[-1] if ":" in at_id else at_id


def _normalize_subclass_of(entry: dict) -> list[str]:
    """rdfs:subClassOf may be a dict or list. Return list of @id strings."""
    sc = entry.get("rdfs:subClassOf")
    if not sc:
        return []
    if isinstance(sc, dict):
        return [sc.get("@id")] if sc.get("@id") else []
    if isinstance(sc, list):
        return [item.get("@id") for item in sc if isinstance(item, dict) and item.get("@id")]
    return []


def _normalize_domain(entry: dict) -> list[str]:
    """schema:domainIncludes — same shape rules as subClassOf."""
    di = entry.get("schema:domainIncludes")
    if not di:
        return []
    if isinstance(di, dict):
        return [di.get("@id")] if di.get("@id") else []
    if isinstance(di, list):
        return [item.get("@id") for item in di if isinstance(item, dict) and item.get("@id")]
    return []


def _build_subclass_chain(graph: list, root: str) -> set[str]:
    """Return @ids of all rdfs:Class entries that descend from `root` via
    rdfs:subClassOf, inclusive of root itself."""
    # Build child→parents adjacency.
    parents_of: dict[str, list[str]] = {}
    for entry in graph:
        if not isinstance(entry, dict):
            continue
        if entry.get("@type") != "rdfs:Class":
            continue
        eid = entry.get("@id")
        if not eid:
            continue
        parents_of[eid] = _normalize_subclass_of(entry)
    # BFS down: for each entry, walk up parents and see if root is reached.
    descendants: set[str] = {root}
    changed = True
    while changed:
        changed = False
        for eid, parents in parents_of.items():
            if eid in descendants:
                continue
            if any(p in descendants for p in parents):
                descendants.add(eid)
                changed = True
    return descendants


def _build_body_for_type(entry: dict) -> str:
    text = _strip_html(entry.get("rdfs:comment") or "")
    if len(text) > _BODY_MAX_CHARS:
        text = text[:_BODY_MAX_CHARS].rsplit(" ", 1)[0].rstrip(",.;:—-") + "…"
    return f"<p>{_escape(text)}</p>" if text else ""


def _build_body_for_property(entry: dict, range_includes: list[str]) -> str:
    text = _strip_html(entry.get("rdfs:comment") or "")
    if range_includes:
        ranges = ", ".join(_short_name(r) for r in range_includes[:6])
        prefix = f"Range: {ranges}. "
        text = prefix + text
    if len(text) > _BODY_MAX_CHARS:
        text = text[:_BODY_MAX_CHARS].rsplit(" ", 1)[0].rstrip(",.;:—-") + "…"
    return f"<p>{_escape(text)}</p>" if text else ""


def fetch_candidates(conn: sqlite3.Connection, source_row, max_new: int | None = None) -> list[dict]:
    cache_dir = Path("data/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / CACHE_FILENAME

    headers = {"User-Agent": _USER_AGENT, "Accept": "application/ld+json"}
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

    graph = data.get("@graph") or []
    root = "schema:WebPage"

    # Types descending from WebPage (inclusive).
    type_descendants = _build_subclass_chain(graph, root)

    existing_urls = {r[0] for r in conn.execute(
        "SELECT source_url FROM sub_considerations WHERE source_url LIKE 'https://schema.org/%'"
    ).fetchall()}

    candidates: list[dict] = []

    # Pass 1: Types.
    for entry in graph:
        if not isinstance(entry, dict):
            continue
        if entry.get("@type") != "rdfs:Class":
            continue
        eid = entry.get("@id")
        if eid not in type_descendants:
            continue
        name = _short_name(eid)
        label = entry.get("rdfs:label") or name
        if isinstance(label, dict):
            label = label.get("@value") or name
        url = f"https://schema.org/{name}"
        if url in existing_urls:
            continue
        comment = _strip_html(entry.get("rdfs:comment") or "")
        first_sentence = re.split(r"(?<=[.!?])\s", comment, maxsplit=1)[0] if comment else ""
        one_liner = f"schema:{name} — {first_sentence[:200]}" if first_sentence else f"schema:{name}"
        if len(one_liner) > 240:
            one_liner = one_liner[:237] + "…"
        candidates.append({
            "slug": f"schemaorg-type-{name.lower()}",
            "one_liner": one_liner,
            "body": _build_body_for_type(entry),
            "source_name": SOURCE_NAME,
            "source_url": url,
            "source_title": f"schema:{name}",
            "source_date": SCHEMA_DATE,
        })
        if max_new and len(candidates) >= max_new:
            return candidates

    # Pass 2: Properties whose domain includes WebPage or a descendant.
    for entry in graph:
        if not isinstance(entry, dict):
            continue
        if entry.get("@type") != "rdf:Property":
            continue
        domains = _normalize_domain(entry)
        if not any(d in type_descendants for d in domains):
            continue
        eid = entry.get("@id")
        name = _short_name(eid) if eid else None
        if not name:
            continue
        url = f"https://schema.org/{name}"
        if url in existing_urls:
            continue
        range_includes = _normalize_domain({"schema:domainIncludes": entry.get("schema:rangeIncludes")})
        comment = _strip_html(entry.get("rdfs:comment") or "")
        first_sentence = re.split(r"(?<=[.!?])\s", comment, maxsplit=1)[0] if comment else ""
        one_liner = f"schema:{name} property — {first_sentence[:200]}" if first_sentence else f"schema:{name} property"
        if len(one_liner) > 240:
            one_liner = one_liner[:237] + "…"
        candidates.append({
            "slug": f"schemaorg-prop-{name.lower()}",
            "one_liner": one_liner,
            "body": _build_body_for_property(entry, range_includes),
            "source_name": SOURCE_NAME,
            "source_url": url,
            "source_title": f"schema:{name}",
            "source_date": SCHEMA_DATE,
        })
        if max_new and len(candidates) >= max_new:
            return candidates

    return candidates
