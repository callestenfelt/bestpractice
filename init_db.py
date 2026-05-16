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

# (slug, label, definition, schema_org_type, synonyms, icon)
# Order mirrors the prototype v3 sidebar: design's intentional grouping
# (auth near landing; confirmation after checkout; etc.). Seed display_order
# follows this order via Session 8's upsert in seed_taxonomies().
PAGE_TYPES: list[tuple[str, str, str, str | None, list[str], str]] = [
    ("start-page",          "Start Page",           "The site's main entry point, broad in scope, multiple audiences",    None,                 ["Homepage", "front page"],                                                          "ph-house"),
    ("landing-page",        "Landing Page",         "Focused single-purpose page for a campaign or referral source",      None,                 ["Campaign page"],                                                                   "ph-flag-banner"),
    ("auth-page",           "Authentication Page",  "Authentication flow — login, sign-up, password reset",                None,                 ["Login page", "sign-in page", "sign-up page", "register page", "password reset"],   "ph-sign-in"),
    ("article-page",        "Article Page",         "A single piece of editorial content, usually long-form",              "Article",            ["Post", "blog post", "story"],                                                      "ph-article"),
    ("collection-page",     "Collection Page",      "A list or grid of items (articles, products, cases)",                 "CollectionPage",     ["List page", "index", "archive"],                                                   "ph-squares-four"),
    ("item-page",           "Item Page",            "Detail view of a single thing (product, project, person)",            "ItemPage",           ["Detail page", "product page"],                                                     "ph-package"),
    ("pricing-page",        "Pricing Page",         "Plan comparison and price presentation, usually with CTA per tier",   None,                 ["Plans page", "tariffs", "subscription page"],                                      "ph-currency-circle-dollar"),
    ("profile-page",        "Profile Page",         "A page representing a person, team, or org",                          "ProfilePage",        ["Bio page", "team member"],                                                         "ph-user-circle"),
    ("search-results-page", "Search Results Page",  "Results returned from a user query",                                  "SearchResultsPage",  ["SERP", "search page"],                                                             "ph-list-magnifying-glass"),
    ("faq-page",            "FAQ Page",             "Structured Q&A page",                                                 "FAQPage",            ["Help", "support page"],                                                            "ph-question"),
    ("about-page",          "About Page",           "Information about the organization",                                  "AboutPage",          ["Company", "who-we-are"],                                                           "ph-info"),
    ("contact-page",        "Contact Page",         "Contact information and forms",                                       "ContactPage",        ["Get in touch"],                                                                    "ph-envelope-simple"),
    ("checkout-page",       "Checkout Page",        "Multi-step purchase or signup completion",                            "CheckoutPage",       ["Cart", "conversion flow"],                                                         "ph-shopping-cart-simple"),
    ("confirmation-page",   "Confirmation Page",    "Post-action page confirming a completed transaction or submission",   None,                 ["Thank-you page", "receipt page", "success page", "order complete"],                "ph-check-circle"),
    ("event-page",          "Event Page",           "Detail page for a single event",                                      "Event",              ["Event detail", "happening"],                                                       "ph-calendar-check"),
    ("legal-page",          "Legal Page",           "Privacy, terms, accessibility statements",                            None,                 ["Policy page"],                                                                     "ph-scales"),
    ("cookie-page",         "Cookie Page",          "Cookie policy and consent details",                                   None,                 ["Cookie policy", "cookie notice"],                                                  "ph-cookie"),
    ("error-page",          "Error Page",           "500, offline, maintenance and other non-404 error states",            None,                 ["Empty state page"],                                                                "ph-warning-octagon"),
    ("404-page",            "404 Page",             "Page shown when a requested URL doesn't exist, with discovery aids",  None,                 ["Not found page", "Page not found", "missing page"],                                "ph-binoculars"),
    ("dashboard-page",      "Dashboard",            "Authenticated overview with personalized data",                       None,                 ["Account home"],                                                                    "ph-gauge"),
    ("site-wide",           "Site-wide",            "Considerations that apply across all pages",                          None,                 ["Global", "cross-cutting"],                                                         "ph-globe"),
]

# (slug, label, definition, synonyms)
# (slug, label, definition, synonyms, icon)
# Order mirrors prototype v3 sidebar (form controls clustered; data-display
# clustered; loading-state cluster; etc.). Seed display_order follows.
# "Loader" dropped from skeleton's synonyms since `loader` is its own slug now
# (same cleanup as the spinner/Loader split in Session 8).
COMPONENTS: list[tuple[str, str, str, list[str], str]] = [
    ("header",         "Header",         "Top-of-page site bar, usually persistent",                                ["Masthead", "top bar"],                                                                  "ph-text-h-one"),
    ("footer",         "Footer",         "Bottom-of-page persistent content",                                       ["Bottom bar"],                                                                           "ph-arrow-line-down"),
    ("navigation",     "Navigation",     "Primary site navigation",                                                 ["Nav", "menu", "main nav"],                                                              "ph-compass"),
    ("menu-bar",       "Menu Bar",       "Horizontal bar of top-level menus, desktop-style",                        ["Application menu", "command bar"],                                                      "ph-list"),
    ("breadcrumb",     "Breadcrumb",     "Path-style location indicator",                                           ["Breadcrumbs", "trail"],                                                                 "ph-caret-right"),
    ("hero",           "Hero",           "Large lead block at top of page",                                         ["Banner", "splash", "jumbotron"],                                                        "ph-image-square"),
    ("eyebrow",        "Eyebrow",        "Short label above a heading",                                             ["Kicker", "supertitle", "overline"],                                                     "ph-text-aa"),
    ("card",           "Card",           "Self-contained content tile with title, body, optional media",           ["Tile", "panel"],                                                                        "ph-cards"),
    ("list",           "List",           "Vertical sequence of related items, ordered or unordered",               ["Bullet list", "numbered list", "ordered list", "unordered list", "ul", "ol"],           "ph-list-bullets"),
    ("button",         "Button",         "Triggerable action element",                                              ["CTA", "action"],                                                                        "ph-cursor-click"),
    ("copy-link-button","Copy Link Button","Button that copies a URL or text to the clipboard, usually with confirmation feedback", ["Share link button", "copy URL", "copy to clipboard"],                       "ph-copy"),
    ("link",           "Link",           "Inline navigation element",                                               ["Anchor"],                                                                               "ph-link-simple"),
    ("form",           "Form",           "Grouped input fields with submission",                                    [],                                                                                       "ph-clipboard-text"),
    ("input-field",    "Input Field",    "Single text/number/etc. input",                                           ["Text input", "field"],                                                                  "ph-text-t"),
    ("textarea",       "Textarea",       "Multi-line text input",                                                   ["Multiline input", "text area", "long text"],                                            "ph-text-align-left"),
    ("select",         "Select",         "Single-choice dropdown",                                                  ["Dropdown", "picker"],                                                                   "ph-caret-down"),
    ("combobox",       "Combobox",       "Text input with filterable suggestion list",                              ["Autocomplete", "type-ahead", "search select"],                                          "ph-magnifying-glass-plus"),
    ("file-upload",    "File Upload",    "Input control for selecting and uploading files",                         ["File input", "uploader", "drop zone", "dropzone"],                                      "ph-upload-simple"),
    ("checkbox",       "Checkbox",       "Multi-select option",                                                     ["Tickbox"],                                                                              "ph-check-square"),
    ("radio-group",    "Radio Group",    "Single-select from visible options",                                      ["Radio buttons"],                                                                        "ph-radio-button"),
    ("toggle",         "Toggle",         "On/off switch",                                                           ["Switch"],                                                                               "ph-toggle-left"),
    ("toggle-group",   "Toggle Group",   "Set of toggle buttons where one or more can be active",                   ["Button group", "segmented control"],                                                    "ph-toggle-right"),
    ("slider",         "Slider",         "Input control for selecting a value within a range",                      ["Range input", "range slider"],                                                          "ph-sliders"),
    ("date-picker",    "Date Picker",    "Input control for selecting a date or date range",                        ["Date input", "date field"],                                                             "ph-calendar-blank"),
    ("modal",          "Modal",          "Overlay that blocks the page until dismissed",                            ["Dialog", "popup", "lightbox"],                                                          "ph-app-window"),
    ("popover",        "Popover",        "Floating panel anchored to a trigger element",                            ["Flyout", "floating panel"],                                                             "ph-chat-circle"),
    ("dropdown-menu",  "Dropdown Menu",  "Menu of actions or links revealed by clicking a trigger",                 ["Action menu", "context menu", "kebab menu"],                                            "ph-dots-three-vertical"),
    ("tooltip",        "Tooltip",        "Hover/focus-triggered short hint",                                        ["Hint"],                                                                                 "ph-info"),
    ("tabs",           "Tabs",           "Switchable panels in the same space",                                     ["Tab group"],                                                                            "ph-rows"),
    ("stepper",        "Stepper",        "Multi-step process indicator with per-step navigation",                   ["Wizard", "step indicator", "progress steps"],                                           "ph-list-numbers"),
    ("accordion",      "Accordion",      "Expandable/collapsible content section",                                  ["Disclosure", "expander"],                                                               "ph-caret-circle-down"),
    ("table",          "Table",          "Tabular data display",                                                    ["Data grid"],                                                                            "ph-table"),
    ("chart",          "Chart",          "Visual representation of data — bars, lines, pies, scatter, etc.",         ["Graph", "data visualization", "data viz", "plot"],                                      "ph-chart-line-up"),
    ("stat",           "Stat",           "Single-metric display with value, label, and optional delta",             ["Metric", "KPI", "stat tile", "number"],                                                 "ph-trend-up"),
    ("pagination",     "Pagination",     "Page-by-page navigation through a list",                                  ["Pager"],                                                                                "ph-caret-double-right"),
    ("filter",         "Filter",         "Narrow a list by criteria",                                               ["Faceted search", "refinement"],                                                         "ph-funnel"),
    ("sort",           "Sort",           "Reorder a list by criteria",                                              ["Sorting controls"],                                                                     "ph-arrows-down-up"),
    ("search",         "Search",         "Query input and result trigger",                                          ["Site search"],                                                                          "ph-magnifying-glass"),
    ("scroll-area",    "Scroll Area",    "Container with styled scrollbars for overflowing content",                ["Scroll container"],                                                                     "ph-arrows-vertical"),
    ("separator",      "Separator",      "Visual divider between content or controls",                              ["Divider", "rule", "hr"],                                                                "ph-minus"),
    ("toast",          "Toast",          "Transient non-blocking message",                                          ["Snackbar", "notification"],                                                             "ph-bell"),
    ("alert",          "Alert",          "Persistent in-page status message",                                       ["Banner alert", "callout"],                                                              "ph-warning"),
    ("service-message","Service Message","Site-wide informational banner about temporary status",                   ["Site banner", "announcement banner", "VMA"],                                            "ph-megaphone"),
    ("cookie-banner",  "Cookie Banner",  "Consent UI for cookie or tracking preferences",                           ["Consent banner", "consent dialog", "cookie consent", "cookie notice"],                  "ph-shield-check"),
    ("micro-feedback", "Micro Feedback", "Lightweight feedback prompt for a single binary or short-tap response",   ["Was this helpful", "thumbs up/down", "quick feedback", "reaction"],                     "ph-thumbs-up"),
    ("progress-bar",   "Progress Bar",   "Visual indicator of completion or determinate state",                     ["Progress indicator"],                                                                   "ph-spinner-gap"),
    ("spinner",        "Spinner",        "Small indeterminate animated indicator, usually inline",                  ["Loading spinner", "activity indicator", "throbber"],                                    "ph-circle-notch"),
    ("loader",         "Loader",         "Page or section-level loading state, often blocking with optional message", ["Page loader", "loading overlay", "loading screen", "full-page loader"],                "ph-hourglass"),
    ("badge",          "Badge",          "Small read-only status or label indicator",                               ["Pill", "label"],                                                                        "ph-seal-check"),
    ("chip",           "Chip",           "Compact interactive element representing an input, attribute, or filter", ["Token", "tag (interactive)"],                                                           "ph-tag"),
    ("rating",         "Rating",         "User-facing rating control or display, usually star-based",               ["Star rating", "score", "stars"],                                                        "ph-star"),
    ("video",          "Video",          "Embedded or hosted video",                                                [],                                                                                       "ph-play-circle"),
    ("audio",          "Audio",          "Embedded audio player with transport controls",                           ["Audio player", "podcast player", "sound clip"],                                         "ph-speaker-high"),
    ("image",          "Image",          "Static image with semantics (alt, caption)",                              ["Picture"],                                                                              "ph-image"),
    ("icon",           "Icon",           "Small symbolic graphic",                                                  ["Glyph", "symbol"],                                                                      "ph-shapes"),
    ("carousel",       "Carousel",       "Horizontally scrollable sequence of content slides",                      ["Slider", "slideshow", "rotator"],                                                       "ph-slideshow"),
    ("gallery",        "Image Gallery",  "Grid or lightbox collection of images for browsing",                      ["Image grid", "photo gallery", "lightbox"],                                              "ph-images"),
    ("map",            "Map",            "Embedded geographic map, usually interactive",                            ["Map embed", "location map"],                                                            "ph-map-trifold"),
    ("code-block",     "Code Block",     "Formatted block of code, usually monospaced and syntax-highlighted",      ["Code snippet", "pre block", "syntax block"],                                            "ph-code"),
    ("calendar",       "Calendar",       "View of dates in month/week/day format, often with events",               ["Schedule view", "agenda view"],                                                         "ph-calendar-dots"),
    ("avatar",         "Avatar",         "Circular or rounded image representing a person or entity",               ["Profile picture", "user image"],                                                        "ph-user"),
    ("shopping-cart",  "Shopping Cart",  "Summary of items selected for purchase, with quantity and price",         ["Cart", "basket", "bag", "mini cart"],                                                   "ph-shopping-cart"),
    ("skeleton",       "Skeleton",       "Loading placeholder shape",                                               ["Shimmer"],                                                                              "ph-rectangle-dashed"),
]


DEFAULT_SOURCES: list[tuple[str, str, str, dict]] = [
    # (name, type, url, config_dict). Seeded once via INSERT OR IGNORE keyed
    # on URL; operator can prune via /admin/sources without these reappearing.
    # The v1 RSS roster per PROJECT.md §5.2 — four high-signal primary
    # sources. CSS-Tricks / Smashing / MDN Blog were the Session 10 first-
    # cut but moved to §5.4 future; they stay in the DB (paused) for any
    # already-ingested rows but are not re-seeded on a fresh init_db.
    ("web.dev",                "rss", "https://web.dev/static/blog/feed.xml", {}),
    # PROJECT.md §5.2 lists this as /feed.xml; that URL 404s in practice.
    # /feed/feed.xml is the actually-served canonical Jekyll output.
    ("The A11y Project",       "rss", "https://www.a11yproject.com/feed/feed.xml", {}),
    ("Nielsen Norman Group",   "rss", "https://www.nngroup.com/feed/rss/", {}),
    ("Google Search Central",  "rss", "https://developers.google.com/search/blog/feed.xml", {}),

    # Structured sources per PROJECT.md §5.1. Each carries {"adapter": "<module>"}
    # under ingestors/. collect_structured.py dispatches by that key.
    ("W3C WCAG 2.2", "structured",
     "https://www.w3.org/WAI/WCAG22/wcag.json",
     {"adapter": "wcag"}),
    ("Schema.org WebPage", "structured",
     "https://schema.org/version/latest/schemaorg-current-https.jsonld",
     {"adapter": "schema_org"}),
    # caniuse cap of 25 per run absorbs the 554-feature first-fetch flood
    # across multiple runs; URL dedup means re-runs don't double-ingest.
    ("caniuse", "structured",
     "https://raw.githubusercontent.com/Fyrd/caniuse/main/data.json",
     {"adapter": "caniuse"}),
    ("OWASP Top 10", "structured",
     "https://raw.githubusercontent.com/OWASP/Top10/master/2021/docs/en/",
     {"adapter": "owasp"}),
    ("GOV.UK Design System", "structured",
     "https://github.com/alphagov/govuk-design-system",
     {"adapter": "govuk"}),
]

# The ingest inbox is a placeholder consideration that pending sub_considerations
# attach to before scoring routes them to a real home. Lives under site-wide so
# it never shows up on a real read view (subs are status='pending' until scoring).
INBOX_CONSIDERATION = {
    "slug": "ingest-inbox",
    "parent_type": "page_type",
    "parent_slug": "site-wide",
    "title": "Ingest inbox",
    "intro": "Placeholder home for freshly ingested items awaiting Groq scoring.",
    "group_label": "Inbox",
    "group_slug": "inbox",
    "group_order": 998,
    "display_order": 0,
}

# Site-wide consideration scaffolds. Each is an empty "container" — title +
# intro, no sub_considerations seeded — to advertise the cross-cutting topic
# in the picker so the editor has a home to Edit-and-approve pending items
# into (OWASP → Security, INP/CWV → Performance, GDPR/cookie → Privacy, etc.).
# All share the same group identity as the existing sw-contrast / sw-keyboard
# rows (group_slug='site-wide', group_label='Site-wide considerations',
# group_order=6) so all 8 considerations render under one section header on
# /page-type/site-wide.
SITE_WIDE_SCAFFOLDS: list[dict] = [
    {
        "slug": "sw-security",
        "title": "Security",
        "intro": "Cross-cutting protections against unauthorized access, data exposure, and injection. Owns CSP, CSRF, session handling, XSS-prevention defaults, and the OWASP Top 10 surface across page types.",
        "display_order": 3,
    },
    {
        "slug": "sw-privacy",
        "title": "Privacy & consent",
        "intro": "User data minimization, lawful basis, consent collection and storage, third-party script isolation. Tracks GDPR / ePrivacy obligations as a site-wide concern, layered onto every page type.",
        "display_order": 4,
    },
    {
        "slug": "sw-performance",
        "title": "Performance",
        "intro": "Core Web Vitals targets and the patterns that meet them: image loading strategy, font loading, JS bundling discipline, render-blocking budget. Performance is owned at the site level even though pages express it.",
        "display_order": 5,
    },
    {
        "slug": "sw-error-handling",
        "title": "Error handling",
        "intro": "Global error patterns: how the site responds to 401/403/404/500, offline states, partial failures, and unexpected exceptions. The shared error posture across all routes — distinct from per-page-type error states.",
        "display_order": 6,
    },
    {
        "slug": "sw-measurement",
        "title": "Measurement & analytics",
        "intro": "Event taxonomy, consent-gated tracking, sampling, dashboards. The data layer that lets the team know whether changes worked. Lives site-wide because page-type instrumentation derives from this scaffold.",
        "display_order": 7,
    },
    {
        "slug": "sw-i18n",
        "title": "Internationalization",
        "intro": "lang attribute, locale formatting, RTL support, language switcher patterns. Site-wide because i18n is impossible to retrofit per page-type — the scaffolding lives once for the whole product.",
        "display_order": 8,
    },
]


# Page-type categories — virtual umbrellas grouping several page_types so a
# consideration can attach to "all pages with a header" rather than picking
# each page_type. (slug, label, definition, [member page_type slugs]).
# Membership is editorial; tweak via SQL if the heuristic feels wrong.
PAGE_TYPE_CATEGORIES: list[tuple[str, str, str, list[str]]] = [
    ("has-header", "Has a header", "Pages that render a top-of-page header with title/H1 and primary nav. Almost every page-type except thin system shells.",
     ["start-page", "landing-page", "auth-page", "article-page", "collection-page",
      "item-page", "pricing-page", "profile-page", "search-results-page", "faq-page",
      "about-page", "contact-page", "checkout-page", "confirmation-page",
      "event-page", "legal-page", "cookie-page", "dashboard-page"]),
    ("transactional", "Transactional flow", "Pages that complete a transaction or session boundary — sign up, pay, confirm, manage. Strong overlap with form components and security considerations.",
     ["auth-page", "checkout-page", "confirmation-page", "dashboard-page"]),
    ("content-rich", "Long-form content", "Pages built around readable narrative or reference text. Heading hierarchy, typography, source attribution, reading length all matter most here.",
     ["article-page", "faq-page", "about-page", "legal-page", "cookie-page"]),
    ("index-style", "Lists / indexes", "Pages whose primary content is a collection or list — empty states, sort/filter, pagination, item-card density.",
     ["start-page", "landing-page", "collection-page", "search-results-page"]),
    ("system-page", "System / utility", "Pages that exist for site mechanics rather than core product content — error states, legal notices, cookie consent details. Thin chrome, no engagement metrics.",
     ["error-page", "404-page", "cookie-page", "legal-page"]),
    ("authenticated", "Behind authentication", "Pages users only see after signing in. Session handling, identity surfaces, and privacy considerations weigh heaviest here.",
     ["dashboard-page", "profile-page", "auth-page"]),
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

    # Session 9: icon column on page_types and components (Phosphor glyph slug).
    existing_pt = {row[1] for row in cur.execute("PRAGMA table_info(page_types)").fetchall()}
    if "icon" not in existing_pt:
        cur.execute("ALTER TABLE page_types ADD COLUMN icon TEXT")
    existing_cmp = {row[1] for row in cur.execute("PRAGMA table_info(components)").fetchall()}
    if "icon" not in existing_cmp:
        cur.execute("ALTER TABLE components ADD COLUMN icon TEXT")

    # Session 10: RFC 7232 conditional-GET caching columns on sources.
    existing_src = {row[1] for row in cur.execute("PRAGMA table_info(sources)").fetchall()}
    if "etag" not in existing_src:
        cur.execute("ALTER TABLE sources ADD COLUMN etag TEXT")
    if "last_modified" not in existing_src:
        cur.execute("ALTER TABLE sources ADD COLUMN last_modified TEXT")
    if "last_fetched" not in existing_src:
        cur.execute("ALTER TABLE sources ADD COLUMN last_fetched TEXT")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_sources_url ON sources(url)")

    # 2026-05-16 data fix: an unescaped <title> in the article-page fixture
    # closed the head's title tag mid-body, swallowing every later element
    # including the <script> tags. Replace with an escaped <code>&lt;title&gt;</code>.
    bad = "Match the H1 to the <title> element unless SEO demands a longer title."
    good = "Match the H1 to the <code>&lt;title&gt;</code> element unless SEO demands a longer title."
    cur.execute(
        "UPDATE sub_considerations SET one_liner = ? WHERE one_liner = ?",
        (good, bad),
    )

    # Session 12: backfill consideration_destinations from the legacy
    # (parent_type, parent_slug) pair on considerations. Idempotent —
    # INSERT OR IGNORE keyed on the composite primary key. Only runs
    # for rows that don't have a destination row yet, so future edits
    # via the admin UI aren't clobbered. The columns stay on
    # considerations for backward-compat reads; new code reads the join.
    cur.execute(
        """INSERT OR IGNORE INTO consideration_destinations
               (consideration_id, dest_kind, dest_slug)
           SELECT id, parent_type, parent_slug
             FROM considerations
            WHERE id NOT IN (
                  SELECT consideration_id FROM consideration_destinations
            )"""
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

    for order, (slug, label, definition, schema_org, syns, icon) in enumerate(PAGE_TYPES, start=1):
        cur.execute(
            "INSERT OR IGNORE INTO page_types (slug, label, definition, schema_org_type, icon, display_order) VALUES (?, ?, ?, ?, ?, ?)",
            (slug, label, definition, schema_org, icon, order),
        )
        cur.execute(
            "UPDATE page_types SET label=?, definition=?, schema_org_type=?, icon=?, display_order=? WHERE slug=?",
            (label, definition, schema_org, icon, order, slug),
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

    for order, (slug, label, definition, syns, icon) in enumerate(COMPONENTS, start=1):
        cur.execute(
            "INSERT OR IGNORE INTO components (slug, label, definition, icon, display_order) VALUES (?, ?, ?, ?, ?)",
            (slug, label, definition, icon, order),
        )
        cur.execute(
            "UPDATE components SET label=?, definition=?, icon=?, display_order=? WHERE slug=?",
            (label, definition, icon, order, slug),
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


def seed_inbox(conn: sqlite3.Connection) -> int:
    """Ensure the ingest-inbox consideration exists. Returns its id."""
    cur = conn.cursor()
    now = now_iso()
    row = cur.execute(
        "SELECT id FROM considerations WHERE parent_type=? AND parent_slug=? AND slug=?",
        (INBOX_CONSIDERATION["parent_type"], INBOX_CONSIDERATION["parent_slug"], INBOX_CONSIDERATION["slug"]),
    ).fetchone()
    if row:
        return row[0]
    cur.execute(
        """INSERT INTO considerations
               (slug, parent_type, parent_slug, title, intro,
                group_label, group_slug, group_order, display_order,
                status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', ?, ?)""",
        (INBOX_CONSIDERATION["slug"], INBOX_CONSIDERATION["parent_type"], INBOX_CONSIDERATION["parent_slug"],
         INBOX_CONSIDERATION["title"], INBOX_CONSIDERATION["intro"],
         INBOX_CONSIDERATION["group_label"], INBOX_CONSIDERATION["group_slug"],
         INBOX_CONSIDERATION["group_order"], INBOX_CONSIDERATION["display_order"],
         now, now),
    )
    conn.commit()
    return cur.lastrowid


def seed_categories(conn: sqlite3.Connection) -> tuple[int, int]:
    """Seed PAGE_TYPE_CATEGORIES + their memberships idempotently.

    Categories: upsert by slug (label/definition/display_order are owned by
    PAGE_TYPE_CATEGORIES; re-running keeps them in sync if the source list
    changes).

    Memberships: clear-then-fill per category so a removed page-type
    actually disappears from the category on next seed. Mirrors the
    synonyms-seed pattern in seed_taxonomies().

    Returns (categories_count, memberships_count) for logging."""
    cur = conn.cursor()
    cat_count = 0
    mem_count = 0
    for order, (slug, label, definition, members) in enumerate(PAGE_TYPE_CATEGORIES, start=1):
        cur.execute(
            "INSERT OR IGNORE INTO page_type_categories (slug, label, definition, display_order) VALUES (?, ?, ?, ?)",
            (slug, label, definition, order),
        )
        cur.execute(
            "UPDATE page_type_categories SET label=?, definition=?, display_order=? WHERE slug=?",
            (label, definition, order, slug),
        )
        cat_count += 1
        cur.execute("DELETE FROM page_type_in_category WHERE category_slug=?", (slug,))
        for pt_slug in members:
            cur.execute(
                "INSERT OR IGNORE INTO page_type_in_category (category_slug, page_type_slug) VALUES (?, ?)",
                (slug, pt_slug),
            )
            mem_count += 1
    conn.commit()
    return cat_count, mem_count


def seed_site_wide_scaffolds(conn: sqlite3.Connection) -> int:
    """Seed empty site-wide consideration containers from SITE_WIDE_SCAFFOLDS.
    Idempotent — checks (parent_type, parent_slug, slug) and only inserts
    missing rows. Title and intro are NOT overwritten on re-runs so a
    later edit via /admin/considerations/<slug> isn't clobbered. Returns
    number of rows added this run."""
    cur = conn.cursor()
    now = now_iso()
    added = 0
    for scaffold in SITE_WIDE_SCAFFOLDS:
        row = cur.execute(
            "SELECT id FROM considerations WHERE parent_type='page_type' AND parent_slug='site-wide' AND slug=?",
            (scaffold["slug"],),
        ).fetchone()
        if row:
            continue
        cur.execute(
            """INSERT INTO considerations
                   (slug, parent_type, parent_slug, title, intro,
                    group_label, group_slug, group_order, display_order,
                    status, created_at, updated_at)
               VALUES (?, 'page_type', 'site-wide', ?, ?,
                       'Site-wide considerations', 'site-wide', 6, ?,
                       'approved', ?, ?)""",
            (scaffold["slug"], scaffold["title"], scaffold["intro"],
             scaffold["display_order"], now, now),
        )
        added += 1
    conn.commit()
    return added


def seed_sources(conn: sqlite3.Connection) -> int:
    """Seed default sources keyed on URL. Idempotent. Returns rows added.
    config_json is written on first insert and never overwritten — so an
    operator can edit a source's adapter config via /admin/sources later
    without it being clobbered on the next re-seed."""
    cur = conn.cursor()
    now = now_iso()
    added = 0
    for name, type_, url, config in DEFAULT_SOURCES:
        before = cur.execute("SELECT COUNT(*) FROM sources WHERE url=?", (url,)).fetchone()[0]
        cur.execute(
            """INSERT OR IGNORE INTO sources (name, type, url, status, config_json, created_at)
               VALUES (?, ?, ?, 'active', ?, ?)""",
            (name, type_, url, json.dumps(config), now),
        )
        if before == 0:
            added += 1
    conn.commit()
    return added


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
        print("seeding page-type categories...")
        cat_count, mem_count = seed_categories(conn)
        print(f"  categories: {cat_count}  memberships: {mem_count}")
        print("seeding ingest inbox...")
        inbox_id = seed_inbox(conn)
        print(f"  inbox consideration id={inbox_id}")
        print("seeding site-wide scaffolds...")
        sw_added = seed_site_wide_scaffolds(conn)
        print(f"  site-wide scaffolds added: {sw_added} (existing rows preserved)")
        print("seeding default sources...")
        added = seed_sources(conn)
        print(f"  sources added: {added} (existing rows preserved)")
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
