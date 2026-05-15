"""One-shot tooling. Parses prototype/page-type.html into fixtures/article_page.json.

Re-run only if the prototype's content changes. The output JSON is committed
so init_db.py doesn't need bs4 as a runtime dependency.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "prototype" / "page-type.html"
DEST = ROOT / "fixtures" / "article_page.json"

# Run anchor: the date that init_db.py will be invoked against.
# Subs flagged `sub--new` in the prototype get last_updated within the
# 14-day window from this anchor. Other subs get spread back further.
NEW_ANCHOR = date(2026, 5, 15)


def inner_html(tag: Tag) -> str:
    """Serialize a tag's children to HTML, preserving inline markup like <code> and <em>."""
    return "".join(str(c) for c in tag.children).strip()


def text_of(tag: Tag) -> str:
    return tag.get_text(" ", strip=True)


def extract_source(metarow: Tag) -> tuple[str, str, str]:
    """Pull (source_name, source_suffix, source_date) from a sub__metarow.

    Layout: chips, then <span class="sub__source"><strong>NAME</strong> ...maybe ' · SUFFIX'</span>,
    then a date span.
    """
    src_span = metarow.find("span", class_="sub__source")
    name = ""
    suffix = ""
    if src_span:
        strong = src_span.find("strong")
        if strong:
            name = text_of(strong)
        # Everything after the <strong> tag is the suffix.
        tail = ""
        seen_strong = False
        for c in src_span.children:
            if isinstance(c, Tag) and c.name == "strong":
                seen_strong = True
                continue
            if seen_strong:
                tail += c.get_text("", strip=False) if isinstance(c, Tag) else str(c)
        suffix = tail.strip().lstrip("·").strip()

    # Date is the last span sibling that is not a chip / dot / source.
    date_text = ""
    for span in metarow.find_all("span", recursive=False):
        classes = span.get("class") or []
        if not classes and re.match(r"^\d{4}-\d{2}-\d{2}$", text_of(span)):
            date_text = text_of(span)

    return name, suffix, date_text


def extract_url(footer: Tag) -> str:
    a = footer.find("a")
    return a["href"] if a and a.has_attr("href") else ""


def extract_source_title(footer: Tag) -> str:
    """Pull the work/article title from the footer (the <em> in 'Source. NAME · <em>TITLE</em>')."""
    em = footer.find("em")
    return text_of(em) if em else ""


def extract_one_liner(top: Tag) -> str:
    one_liner = top.find("span", class_="sub__one-liner")
    if not one_liner:
        return ""
    # Strip the new-dot decoration and sr-only "New. " if present —
    # is-new is computed at render time, not stored.
    for cls in ("sub__newdot",):
        for el in one_liner.find_all("span", class_=cls):
            el.decompose()
    for sr in one_liner.find_all("span", class_="sr-only"):
        if sr.get_text(strip=True).startswith("New"):
            sr.decompose()
    return inner_html(one_liner)


def extract_body(sub: Tag) -> str:
    body = sub.find("div", class_="sub__body")
    if not body:
        return ""
    # Drop the footer; that's source attribution handled separately.
    footer = body.find("div", class_="sub__footer")
    if footer:
        footer.extract()
    # Strip inline style attributes (prototype has some for visual tuning we don't want in prod data).
    for el in body.find_all(True):
        if el.has_attr("style"):
            del el["style"]
    return inner_html(body)


def parse_phases(sub: Tag) -> list[str]:
    raw = sub.get("data-phases", "")
    return [p for p in raw.split() if p]


def main() -> None:
    html = SOURCE.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    groups_out: list[dict] = []
    new_idx = 0  # how many "new"-flagged subs we've seen, for date spreading

    page_main = soup.select_one("div.main")
    assert page_main is not None, "prototype is missing div.main"

    groups = page_main.find_all("section", class_="group")
    for g_order, group in enumerate(groups, start=1):
        group_slug = group.get("data-group", "")
        title_el = group.find("h2", class_="group__title")
        group_label = text_of(title_el) if title_el else group_slug

        considerations_out: list[dict] = []
        considerations = group.find_all("details", class_="consideration", recursive=True)
        for c_order, cons in enumerate(considerations, start=1):
            cons_slug = cons.get("id", "")
            title_el = cons.find("span", class_="consideration__title")
            title = text_of(title_el) if title_el else cons_slug

            subs_out: list[dict] = []
            subs = cons.find_all("details", class_="sub", recursive=True)
            for s_order, sub in enumerate(subs, start=1):
                sub_full_id = sub.get("id", "")
                # IDs are `{cons_slug}.{sub_slug}` per BUILD_NOTES §3 / §4
                sub_slug = sub_full_id.split(".", 1)[1] if "." in sub_full_id else sub_full_id
                is_new = "sub--new" in (sub.get("class") or [])

                top = sub.find("div", class_="sub__top")
                metarow = sub.find("div", class_="sub__metarow")
                footer = sub.find("div", class_="sub__footer")

                one_liner = extract_one_liner(top) if top else ""
                phases = parse_phases(sub)
                src_name, src_suffix, src_date = extract_source(metarow) if metarow else ("", "", "")
                url = extract_url(footer) if footer else ""
                src_title = extract_source_title(footer) if footer else ""
                body = extract_body(sub)

                # last_updated: stamp "new" subs within the 14d window,
                # spread by 3-day intervals so they don't all decay at once.
                if is_new:
                    last_updated = (NEW_ANCHOR - timedelta(days=new_idx * 3)).isoformat()
                    new_idx += 1
                else:
                    # Use the source_date as last_updated if available and outside the new window;
                    # otherwise pin to 30 days ago so it definitely doesn't flag new.
                    if src_date and re.match(r"^\d{4}-\d{2}-\d{2}$", src_date):
                        sd = date.fromisoformat(src_date)
                        if (NEW_ANCHOR - sd).days < 14:
                            last_updated = (NEW_ANCHOR - timedelta(days=30)).isoformat()
                        else:
                            last_updated = src_date
                    else:
                        last_updated = (NEW_ANCHOR - timedelta(days=30)).isoformat()

                subs_out.append({
                    "slug": sub_slug,
                    "one_liner": one_liner,
                    "body": body,
                    "phases": phases,
                    "source_name": src_name,
                    "source_suffix": src_suffix,
                    "source_title": src_title,
                    "source_url": url,
                    "source_date": src_date or None,
                    "last_updated": last_updated,
                    "display_order": s_order,
                })

            considerations_out.append({
                "slug": cons_slug,
                "title": title,
                "intro": "",
                "display_order": c_order,
                "sub_considerations": subs_out,
            })

        groups_out.append({
            "group_slug": group_slug,
            "group_label": group_label,
            "group_order": g_order,
            "considerations": considerations_out,
        })

    fixture = {
        "parent_type": "page_type",
        "parent_slug": "article-page",
        "extracted_at": datetime.utcnow().isoformat() + "Z",
        "new_anchor": NEW_ANCHOR.isoformat(),
        "groups": groups_out,
    }

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(fixture, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    total_cons = sum(len(g["considerations"]) for g in groups_out)
    total_subs = sum(len(c["sub_considerations"]) for g in groups_out for c in g["considerations"])
    print(f"Wrote {DEST.relative_to(ROOT)}")
    print(f"  groups: {len(groups_out)}")
    print(f"  considerations: {total_cons}")
    print(f"  sub-considerations: {total_subs}")
    print(f"  new-flagged subs: {new_idx}")


if __name__ == "__main__":
    main()
