"""Initialise the bestpractice SQLite DB.

Applies schema, seeds the three locked taxonomies from PROJECT.md §2.1-2.3,
and imports fixtures/article_page.json. Idempotent: safe to re-run; uses
INSERT OR IGNORE for taxonomies, skips fixture import if any considerations
already exist for `article-page`.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "schema.sql"
FIXTURE_DIR = ROOT / "fixtures"
FIXTURES = [
    ("page_type", "article-page", FIXTURE_DIR / "article_page.json"),
    ("component", "image",        FIXTURE_DIR / "image_component.json"),
]
DEFAULT_DB = ROOT / "data" / "bestpractice.db"

# ---------- Locked taxonomies (PROJECT.md §2.1-2.3) ----------

PHASES: list[tuple[str, str, str]] = [
    ("strategy",    "Strategy",    "Business goals, KPIs, audience definition, platform decisions"),
    ("concept",     "Concept",     "IA, tone of voice, proof of concept, early structural decisions"),
    ("ux",          "UX",          "User journeys, flows, accessibility intent, wireframing"),
    ("design",      "Design",      "Visual design, design system, typography, color, micro-interactions"),
    ("frontend",    "Frontend",    "Markup, styles, behavior, Core Web Vitals, code quality"),
    ("backend",     "Backend",     "Architecture, APIs, CMS, caching, security"),
    ("content",     "Content",     "Copywriting, content modeling, media optimization"),
    ("seo",         "SEO",         "Technical SEO, on-page, search intent, GEO"),
    ("measurement", "Measurement", "Analytics, tracking, CRO, dashboards"),
    ("maintenance", "Maintenance", "Audits, security updates, CI/CD, monitoring"),
    ("legal",       "Legal",       "Privacy, terms, consent, accessibility statements, and other regulatory considerations"),
]

# (slug, label, definition, schema_org_type, synonyms)
PAGE_TYPES: list[tuple[str, str, str, str | None, list[str]]] = [
    ("start-page",          "Start Page",           "The site's main entry point, broad in scope, multiple audiences", None,                 ["Homepage", "front page"]),
    ("landing-page",        "Landing Page",         "Focused single-purpose page for a campaign or referral source",   None,                 ["Campaign page"]),
    ("article-page",        "Article Page",         "A single piece of editorial content, usually long-form",           "Article",            ["Post", "blog post", "story"]),
    ("collection-page",     "Collection Page",      "A list or grid of items (articles, products, cases)",              "CollectionPage",     ["List page", "index", "archive"]),
    ("item-page",           "Item Page",            "Detail view of a single thing (product, project, person)",         "ItemPage",           ["Detail page", "product page"]),
    ("profile-page",        "Profile Page",         "A page representing a person, team, or org",                       "ProfilePage",        ["Bio page", "team member"]),
    ("search-results-page", "Search Results Page",  "Results returned from a user query",                                "SearchResultsPage",  ["SERP", "search page"]),
    ("faq-page",            "FAQ Page",             "Structured Q&A page",                                                "FAQPage",            ["Help", "support page"]),
    ("about-page",          "About Page",           "Information about the organization",                                 "AboutPage",          ["Company", "who-we-are"]),
    ("contact-page",        "Contact Page",         "Contact information and forms",                                      "ContactPage",        ["Get in touch"]),
    ("checkout-page",       "Checkout Page",        "Multi-step purchase or signup completion",                            "CheckoutPage",       ["Cart", "conversion flow"]),
    ("event-page",          "Event Page",           "Detail page for a single event",                                      "Event",              ["Event detail", "happening"]),
    ("legal-page",          "Legal Page",           "Privacy, terms, accessibility statements",                            None,                 ["Policy page"]),
    ("cookie-page",         "Cookie Page",          "Cookie policy and consent details",                                   None,                 ["Cookie policy", "cookie notice"]),
    ("error-page",          "Error Page",           "500, offline, maintenance and other non-404 error states",            None,                 ["Empty state page"]),
    ("404-page",            "404 Page",             "Page shown when a requested URL doesn't exist, with discovery aids",  None,                 ["Not found page", "Page not found", "missing page"]),
    ("dashboard-page",      "Dashboard",            "Authenticated overview with personalized data",                       None,                 ["Account home"]),
    ("pricing-page",        "Pricing Page",         "Plan comparison and price presentation, usually with CTA per tier",  None,                 ["Plans page", "tariffs", "subscription page"]),
    ("confirmation-page",   "Confirmation Page",    "Post-action page confirming a completed transaction or submission",  None,                 ["Thank-you page", "receipt page", "success page", "order complete"]),
    ("auth-page",           "Authentication Page",  "Authentication flow — login, sign-up, password reset",                None,                 ["Login page", "sign-in page", "sign-up page", "register page", "password reset"]),
    ("site-wide",           "Site-wide",            "Considerations that apply across all pages",                          None,                 ["Global", "cross-cutting"]),
]

# (slug, label, definition, synonyms)
COMPONENTS: list[tuple[str, str, str, list[str]]] = [
    ("header",         "Header",         "Top-of-page site bar, usually persistent",                              ["Masthead", "top bar"]),
    ("footer",         "Footer",         "Bottom-of-page persistent content",                                     ["Bottom bar"]),
    ("navigation",     "Navigation",     "Primary site navigation",                                                ["Nav", "menu", "main nav"]),
    ("menu-bar",       "Menu Bar",       "Horizontal bar of top-level menus, desktop-style",                       ["Application menu", "command bar"]),
    ("breadcrumb",     "Breadcrumb",     "Path-style location indicator",                                          ["Breadcrumbs", "trail"]),
    ("hero",           "Hero",           "Large lead block at top of page",                                        ["Banner", "splash", "jumbotron"]),
    ("eyebrow",        "Eyebrow",        "Short label above a heading",                                            ["Kicker", "supertitle", "overline"]),
    ("card",           "Card",           "Self-contained content tile with title, body, optional media",          ["Tile", "panel"]),
    ("shopping-cart",  "Shopping Cart",  "Summary of items selected for purchase, with quantity and price",        ["Cart", "basket", "bag", "mini cart"]),
    ("button",         "Button",         "Triggerable action element",                                             ["CTA", "action"]),
    ("copy-link-button","Copy Link Button","Button that copies a URL or text to the clipboard, usually with confirmation feedback", ["Share link button", "copy URL", "copy to clipboard"]),
    ("link",           "Link",           "Inline navigation element",                                              ["Anchor"]),
    ("form",           "Form",           "Grouped input fields with submission",                                   []),
    ("input-field",    "Input Field",    "Single text/number/etc. input",                                          ["Text input", "field"]),
    ("textarea",       "Textarea",       "Multi-line text input",                                                   ["Multiline input", "text area", "long text"]),
    ("select",         "Select",         "Single-choice dropdown",                                                  ["Dropdown", "picker"]),
    ("combobox",       "Combobox",       "Text input with filterable suggestion list",                              ["Autocomplete", "type-ahead", "search select"]),
    ("checkbox",       "Checkbox",       "Multi-select option",                                                     ["Tickbox"]),
    ("radio-group",    "Radio Group",    "Single-select from visible options",                                      ["Radio buttons"]),
    ("toggle",         "Toggle",         "On/off switch",                                                            ["Switch"]),
    ("toggle-group",   "Toggle Group",   "Set of toggle buttons where one or more can be active",                   ["Button group", "segmented control"]),
    ("slider",         "Slider",         "Input control for selecting a value within a range",                      ["Range input", "range slider"]),
    ("date-picker",    "Date Picker",    "Input control for selecting a date or date range",                        ["Date input", "date field"]),
    ("file-upload",    "File Upload",    "Input control for selecting and uploading files",                         ["File input", "uploader", "drop zone", "dropzone"]),
    ("modal",          "Modal",          "Overlay that blocks the page until dismissed",                            ["Dialog", "popup", "lightbox"]),
    ("popover",        "Popover",        "Floating panel anchored to a trigger element",                            ["Flyout", "floating panel"]),
    ("dropdown-menu",  "Dropdown Menu",  "Menu of actions or links revealed by clicking a trigger",                 ["Action menu", "context menu", "kebab menu"]),
    ("tooltip",        "Tooltip",        "Hover/focus-triggered short hint",                                         ["Hint"]),
    ("tabs",           "Tabs",           "Switchable panels in the same space",                                      ["Tab group"]),
    ("stepper",        "Stepper",        "Multi-step process indicator with per-step navigation",                    ["Wizard", "step indicator", "progress steps"]),
    ("accordion",      "Accordion",      "Expandable/collapsible content section",                                   ["Disclosure", "expander"]),
    ("list",           "List",           "Vertical sequence of related items, ordered or unordered",                 ["Bullet list", "numbered list", "ordered list", "unordered list", "ul", "ol"]),
    ("code-block",     "Code Block",     "Formatted block of code, usually monospaced and syntax-highlighted",       ["Code snippet", "pre block", "syntax block"]),
    ("table",          "Table",          "Tabular data display",                                                     ["Data grid"]),
    ("chart",          "Chart",          "Visual representation of data — bars, lines, pies, scatter, etc.",         ["Graph", "data visualization", "data viz", "plot"]),
    ("pagination",     "Pagination",     "Page-by-page navigation through a list",                                   ["Pager"]),
    ("filter",         "Filter",         "Narrow a list by criteria",                                                ["Faceted search", "refinement"]),
    ("sort",           "Sort",           "Reorder a list by criteria",                                               ["Sorting controls"]),
    ("search",         "Search",         "Query input and result trigger",                                            ["Site search"]),
    ("scroll-area",    "Scroll Area",    "Container with styled scrollbars for overflowing content",                 ["Scroll container"]),
    ("separator",      "Separator",      "Visual divider between content or controls",                               ["Divider", "rule", "hr"]),
    ("toast",          "Toast",          "Transient non-blocking message",                                            ["Snackbar", "notification"]),
    ("alert",          "Alert",          "Persistent in-page status message",                                          ["Banner alert", "callout"]),
    ("service-message","Service Message","Site-wide informational banner about temporary status",                     ["Site banner", "announcement banner", "VMA"]),
    ("cookie-banner",  "Cookie Banner",  "Consent UI for cookie or tracking preferences",                              ["Consent banner", "consent dialog", "cookie consent", "cookie notice"]),
    ("progress-bar",   "Progress Bar",   "Visual indicator of completion or determinate state",                       ["Progress indicator"]),
    ("spinner",        "Spinner",        "Small indeterminate animated indicator, usually inline",                     ["Loading spinner", "activity indicator", "throbber"]),
    ("loader",         "Loader",         "Page or section-level loading state, often blocking with optional message", ["Page loader", "loading overlay", "loading screen", "full-page loader"]),
    ("badge",          "Badge",          "Small read-only status or label indicator",                                  ["Pill", "label"]),
    ("chip",           "Chip",           "Compact interactive element representing an input, attribute, or filter",   ["Token", "tag (interactive)"]),
    ("stat",           "Stat",           "Single-metric display with value, label, and optional delta",                ["Metric", "KPI", "stat tile", "number"]),
    ("rating",         "Rating",         "User-facing rating control or display, usually star-based",                  ["Star rating", "score", "stars"]),
    ("micro-feedback", "Micro Feedback", "Lightweight feedback prompt for a single binary or short-tap response",      ["Was this helpful", "thumbs up/down", "quick feedback", "reaction"]),
    ("video",          "Video",          "Embedded or hosted video",                                                    []),
    ("audio",          "Audio",          "Embedded audio player with transport controls",                              ["Audio player", "podcast player", "sound clip"]),
    ("image",          "Image",          "Static image with semantics (alt, caption)",                                   ["Picture"]),
    ("icon",           "Icon",           "Small symbolic graphic",                                                        ["Glyph", "symbol"]),
    ("carousel",       "Carousel",       "Horizontally scrollable sequence of content slides",                            ["Slider", "slideshow", "rotator"]),
    ("gallery",        "Image Gallery",  "Grid or lightbox collection of images for browsing",                            ["Image grid", "photo gallery", "lightbox"]),
    ("map",            "Map",            "Embedded geographic map, usually interactive",                                  ["Map embed", "location map"]),
    ("calendar",       "Calendar",       "View of dates in month/week/day format, often with events",                     ["Schedule view", "agenda view"]),
    ("avatar",         "Avatar",         "Circular or rounded image representing a person or entity",                      ["Profile picture", "user image"]),
    ("skeleton",       "Skeleton",       "Loading placeholder shape",                                                       ["Shimmer", "loader"]),
]


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def apply_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    migrate(conn)


def migrate(conn: sqlite3.Connection) -> None:
    """Idempotent column additions + data fixes for DBs that predate a change.

    CREATE TABLE IF NOT EXISTS doesn't touch existing tables, so any new
    column added to schema.sql needs an explicit ALTER here for prod boxes
    that already have the file. Data fixes follow the same shape.
    """
    cur = conn.cursor()
    # PRAGMA table_info columns: (cid, name, type, notnull, dflt_value, pk)
    existing = {row[1] for row in cur.execute("PRAGMA table_info(sub_considerations)").fetchall()}
    if "relevance_score" not in existing:
        cur.execute("ALTER TABLE sub_considerations ADD COLUMN relevance_score INTEGER")

    # 2026-05-16 data fix: an unescaped <title> in the article-page fixture
    # closed the head's title tag mid-body, swallowing every later element
    # including the <script> tags. Replace with an escaped <code>&lt;title&gt;</code>.
    bad = "Match the H1 to the <title> element unless SEO demands a longer title."
    good = "Match the H1 to the <code>&lt;title&gt;</code> element unless SEO demands a longer title."
    cur.execute(
        "UPDATE sub_considerations SET one_liner = ? WHERE one_liner = ?",
        (good, bad),
    )

    conn.commit()


def seed_taxonomies(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    # Taxonomy lists are the source of truth for ordering. UPSERT semantics
    # via INSERT OR IGNORE + UPDATE so that adding a new entry mid-list
    # re-numbers later entries on subsequent seeds (otherwise existing rows
    # would keep stale display_order and the canonical order would scramble).
    for order, (slug, label, definition) in enumerate(PHASES, start=1):
        cur.execute(
            "INSERT OR IGNORE INTO phases (slug, label, definition, display_order) VALUES (?, ?, ?, ?)",
            (slug, label, definition, order),
        )
        cur.execute(
            "UPDATE phases SET label=?, definition=?, display_order=? WHERE slug=?",
            (label, definition, order, slug),
        )

    for order, (slug, label, definition, schema_org, syns) in enumerate(PAGE_TYPES, start=1):
        cur.execute(
            "INSERT OR IGNORE INTO page_types (slug, label, definition, schema_org_type, display_order) VALUES (?, ?, ?, ?, ?)",
            (slug, label, definition, schema_org, order),
        )
        cur.execute(
            "UPDATE page_types SET label=?, definition=?, schema_org_type=?, display_order=? WHERE slug=?",
            (label, definition, schema_org, order, slug),
        )
        cur.execute(
            "DELETE FROM synonyms WHERE entity_type=? AND entity_slug=?",
            ("page_type", slug),
        )
        for s in syns:
            cur.execute(
                "INSERT INTO synonyms (entity_type, entity_slug, synonym) VALUES (?, ?, ?)",
                ("page_type", slug, s),
            )

    for order, (slug, label, definition, syns) in enumerate(COMPONENTS, start=1):
        cur.execute(
            "INSERT OR IGNORE INTO components (slug, label, definition, display_order) VALUES (?, ?, ?, ?)",
            (slug, label, definition, order),
        )
        cur.execute(
            "UPDATE components SET label=?, definition=?, display_order=? WHERE slug=?",
            (label, definition, order, slug),
        )
        cur.execute(
            "DELETE FROM synonyms WHERE entity_type=? AND entity_slug=?",
            ("component", slug),
        )
        for s in syns:
            cur.execute(
                "INSERT INTO synonyms (entity_type, entity_slug, synonym) VALUES (?, ?, ?)",
                ("component", slug, s),
            )

    conn.commit()


def load_fixture(conn: sqlite3.Connection, parent_type: str, parent_slug: str, path: Path) -> int:
    """Idempotently import one fixture file.

    Skips if any considerations already exist for the (parent_type, parent_slug)
    pair. Honours the special-case where a group's `group_slug == 'site-wide'`
    gets rebucketed under `parent_slug='site-wide'` so it can be layered onto
    any parent (PROJECT.md §2.2).
    """
    if not path.exists():
        print(f"  (skip) fixture not found: {path}")
        return 0

    cur = conn.cursor()
    existing = cur.execute(
        "SELECT COUNT(*) FROM considerations WHERE parent_type=? AND parent_slug=?",
        (parent_type, parent_slug),
    ).fetchone()[0]
    # site-wide is a shared bucket fed by the article-page fixture; let other
    # fixtures coexist with it without tripping the skip.
    if existing:
        print(f"  (skip) {parent_type}/{parent_slug} already has {existing} considerations")
        return 0

    fixture = json.loads(path.read_text(encoding="utf-8"))
    fx_parent_type = fixture["parent_type"]
    fx_parent_slug = fixture["parent_slug"]
    if (fx_parent_type, fx_parent_slug) != (parent_type, parent_slug):
        print(f"  (skip) fixture parent mismatch: expected {parent_type}/{parent_slug}, got {fx_parent_type}/{fx_parent_slug}")
        return 0

    inserted_cons = 0
    inserted_subs = 0
    now = now_iso()

    for group in fixture["groups"]:
        group_label = group["group_label"]
        group_slug = group["group_slug"]
        group_order = group["group_order"]
        effective_parent_slug = "site-wide" if group_slug == "site-wide" else fx_parent_slug

        for cons in group["considerations"]:
            cur.execute(
                """INSERT INTO considerations
                       (slug, parent_type, parent_slug, title, intro,
                        group_label, group_slug, group_order, display_order,
                        status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', ?, ?)""",
                (cons["slug"], fx_parent_type, effective_parent_slug, cons["title"], cons.get("intro", ""),
                 group_label, group_slug, group_order, cons["display_order"],
                 now, now),
            )
            cons_id = cur.lastrowid
            inserted_cons += 1

            for sub in cons["sub_considerations"]:
                cur.execute(
                    """INSERT INTO sub_considerations
                           (consideration_id, slug, one_liner, body,
                            source_name, source_suffix, source_title, source_url, source_date,
                            status, display_order, created_at, last_updated)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', ?, ?, ?)""",
                    (cons_id, sub["slug"], sub["one_liner"], sub.get("body", ""),
                     sub.get("source_name", ""), sub.get("source_suffix", ""),
                     sub.get("source_title", ""),
                     sub.get("source_url", ""), sub.get("source_date"),
                     sub["display_order"], now, sub["last_updated"]),
                )
                sub_id = cur.lastrowid
                inserted_subs += 1
                for pos, phase_slug in enumerate(sub.get("phases", []), start=1):
                    cur.execute(
                        "INSERT OR IGNORE INTO sub_consideration_phases (sub_consideration_id, phase_slug, position) VALUES (?, ?, ?)",
                        (sub_id, phase_slug, pos),
                    )

    conn.commit()
    print(f"  {parent_type}/{parent_slug}: considerations={inserted_cons} subs={inserted_subs}")
    return inserted_cons


def rebuild_fts(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    cur.execute("DELETE FROM subs_fts")
    cur.execute(
        """INSERT INTO subs_fts (rowid, one_liner, body, cons_title, cons_intro)
           SELECT s.id, s.one_liner, s.body, c.title, c.intro
             FROM sub_considerations s
             JOIN considerations c ON c.id = s.consideration_id
            WHERE s.status = 'approved' AND c.status = 'approved'"""
    )
    count = cur.execute("SELECT COUNT(*) FROM subs_fts").fetchone()[0]
    conn.commit()
    return count


def main() -> None:
    db_path = Path(os.environ.get("BESTPRACTICE_DB", str(DEFAULT_DB)))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"db: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        print("applying schema...")
        apply_schema(conn)
        print("seeding taxonomies...")
        seed_taxonomies(conn)
        print("loading fixtures...")
        for parent_type, parent_slug, path in FIXTURES:
            load_fixture(conn, parent_type, parent_slug, path)
        print("rebuilding FTS...")
        n = rebuild_fts(conn)
        print(f"  FTS rows: {n}")
    finally:
        conn.close()
    print("done.")


if __name__ == "__main__":
    main()
