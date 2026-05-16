# bestpractice

A personal reference tool for web design and development best practices,
organized by the artifact you're working on (page type, component) rather
than by topic.

This document is the shared brief. Both the design agent and the build agent
read it cover to cover. It is authoritative on **what** bestpractice is and
how it behaves. Visual decisions belong in `DESIGN_HANDOVER.md`. Implementation
decisions belong in `BUILD_HANDOVER.md`.

---

## 1. Vision and audience

bestpractice is a working reference for one user (the project owner, a UX
designer who also writes frontend code). It exists because keeping up with
current best practices across web design and development is genuinely hard:
the field changes, sources are scattered, and most aggregators organize by
topic when the question you actually have is "what should I think about for
*this* kind of page?"

The core inversion: organize knowledge by **page type and component**, not
by discipline. When the user is working on a search results page, they want
to see everything that matters for a search results page — accessibility,
performance, content, SEO, interaction patterns — in one place. Discipline
becomes a filter, not a category.

**Out of scope.** Public launch, multi-user accounts, comments, social
features, monetization, mobile native app, dark mode toggle (light only for
v1). This is a single-user reference tool.

---

## 2. Core concepts and vocabulary

### 2.1 Phases

A phase represents a discipline or project stage. Phases are filterable;
the user toggles them on and off via checkboxes to narrow what they see.

| slug | label | one-line definition |
|---|---|---|
| strategy | Strategy | Business goals, KPIs, audience definition, platform decisions |
| concept | Concept | IA, tone of voice, proof of concept, early structural decisions |
| ux | UX | User journeys, flows, accessibility intent, wireframing |
| design | Design | Visual design, design system, typography, color, micro-interactions |
| frontend | Frontend | Markup, styles, behavior, Core Web Vitals, code quality |
| backend | Backend | Architecture, APIs, CMS, caching, security |
| content | Content | Copywriting, content modeling, media optimization |
| seo | SEO | Technical SEO, on-page, search intent, GEO |
| measurement | Measurement | Analytics, tracking, CRO, dashboards |
| maintenance | Maintenance | Audits, security updates, CI/CD, monitoring |
| legal | Legal | Privacy, terms, consent, accessibility statements, and other regulatory considerations |

### 2.2 Page types

A page type is a kind of page someone builds. The primary organizing axis
of the tool. Schema.org alignment is noted where present.

| slug | label | Schema.org | one-line definition | synonyms |
|---|---|---|---|---|
| start-page | Start Page | (none — `WebSite`) | The site's main entry point, broad in scope, multiple audiences | Homepage, front page |
| landing-page | Landing Page | (none) | Focused single-purpose page for a campaign or referral source | Campaign page |
| article-page | Article Page | `Article` | A single piece of editorial content, usually long-form | Post, blog post, story |
| collection-page | Collection Page | `CollectionPage` | A list or grid of items (articles, products, cases) | List page, index, archive |
| item-page | Item Page | `ItemPage` | Detail view of a single thing (product, project, person) | Detail page, product page |
| profile-page | Profile Page | `ProfilePage` | A page representing a person, team, or org | Bio page, team member |
| search-results-page | Search Results Page | `SearchResultsPage` | Results returned from a user query | SERP, search page |
| faq-page | FAQ Page | `FAQPage` | Structured Q&A page | Help, support page |
| about-page | About Page | `AboutPage` | Information about the organization | Company, who-we-are |
| contact-page | Contact Page | `ContactPage` | Contact information and forms | Get in touch |
| checkout-page | Checkout Page | `CheckoutPage` | Multi-step purchase or signup completion | Cart, conversion flow |
| event-page | Event Page | `Event` | Detail page for a single event | Event detail, happening |
| legal-page | Legal Page | (none) | Privacy, terms, accessibility statements | Policy page |
| cookie-page | Cookie Page | (none) | Cookie policy and consent details | Cookie policy, cookie notice |
| error-page | Error Page | (none) | 500, offline, maintenance and other non-404 error states | Empty state page |
| 404-page | 404 Page | (none) | Page shown when a requested URL doesn't exist, with discovery aids | Not found page, Page not found, missing page |
| dashboard-page | Dashboard | (none) | Authenticated overview with personalized data | Account home |
| pricing-page | Pricing Page | (none) | Plan comparison and price presentation, usually with CTA per tier | Plans page, tariffs, subscription page |
| confirmation-page | Confirmation Page | (none) | Post-action page confirming a completed transaction or submission | Thank-you page, receipt page, success page, order complete |
| auth-page | Authentication Page | (none) | Authentication flow — login, sign-up, password reset | Login page, sign-in page, sign-up page, register page, password reset |
| site-wide | Site-wide | (none) | Considerations that apply across all pages | Global, cross-cutting |

`site-wide` is special: it's not a real page, but a bucket for cross-cutting
considerations (alt text, color contrast, keyboard navigation, etc.) that
the user can layer onto whatever page type they're viewing.

### 2.3 Components

A component is a reusable UI element. Treated like page types — each has
its own set of considerations. Some appear visually on pages (cards,
buttons, heroes), some are interaction primitives (popover, tooltip,
dialog). The distinction doesn't matter for the data model; everything
is a component.

| slug | label | one-line definition | synonyms |
|---|---|---|---|
| header | Header | Top-of-page site bar, usually persistent | Masthead, top bar |
| footer | Footer | Bottom-of-page persistent content | Bottom bar |
| navigation | Navigation | Primary site navigation | Nav, menu, main nav |
| menu-bar | Menu Bar | Horizontal bar of top-level menus, desktop-style | Application menu, command bar |
| breadcrumb | Breadcrumb | Path-style location indicator | Breadcrumbs, trail |
| hero | Hero | Large lead block at top of page | Banner, splash, jumbotron |
| eyebrow | Eyebrow | Short label above a heading | Kicker, supertitle, overline |
| card | Card | Self-contained content tile with title, body, optional media | Tile, panel |
| shopping-cart | Shopping Cart | Summary of items selected for purchase, with quantity and price | Cart, basket, bag, mini cart |
| button | Button | Triggerable action element | CTA, action |
| copy-link-button | Copy Link Button | Button that copies a URL or text to the clipboard, usually with confirmation feedback | Share link button, copy URL, copy to clipboard |
| link | Link | Inline navigation element | Anchor |
| form | Form | Grouped input fields with submission | — |
| input-field | Input Field | Single text/number/etc. input | Text input, field |
| textarea | Textarea | Multi-line text input | Multiline input, text area, long text |
| select | Select | Single-choice dropdown | Dropdown, picker |
| combobox | Combobox | Text input with filterable suggestion list | Autocomplete, type-ahead, search select |
| checkbox | Checkbox | Multi-select option | Tickbox |
| radio-group | Radio Group | Single-select from visible options | Radio buttons |
| toggle | Toggle | On/off switch | Switch |
| toggle-group | Toggle Group | Set of toggle buttons where one or more can be active | Button group, segmented control |
| slider | Slider | Input control for selecting a value within a range | Range input, range slider |
| date-picker | Date Picker | Input control for selecting a date or date range | Date input, date field |
| file-upload | File Upload | Input control for selecting and uploading files | File input, uploader, drop zone, dropzone |
| modal | Modal | Overlay that blocks the page until dismissed | Dialog, popup, lightbox |
| popover | Popover | Floating panel anchored to a trigger element | Flyout, floating panel |
| dropdown-menu | Dropdown Menu | Menu of actions or links revealed by clicking a trigger | Action menu, context menu, kebab menu |
| tooltip | Tooltip | Hover/focus-triggered short hint | Hint |
| tabs | Tabs | Switchable panels in the same space | Tab group |
| stepper | Stepper | Multi-step process indicator with per-step navigation | Wizard, step indicator, progress steps |
| accordion | Accordion | Expandable/collapsible content section | Disclosure, expander |
| list | List | Vertical sequence of related items, ordered or unordered | Bullet list, numbered list, ordered list, unordered list, ul, ol |
| code-block | Code Block | Formatted block of code, usually monospaced and syntax-highlighted | Code snippet, pre block, syntax block |
| table | Table | Tabular data display | Data grid |
| chart | Chart | Visual representation of data — bars, lines, pies, scatter, etc. | Graph, data visualization, data viz, plot |
| pagination | Pagination | Page-by-page navigation through a list | Pager |
| filter | Filter | Narrow a list by criteria | Faceted search, refinement |
| sort | Sort | Reorder a list by criteria | Sorting controls |
| search | Search | Query input and result trigger | Site search |
| scroll-area | Scroll Area | Container with styled scrollbars for overflowing content | Scroll container |
| separator | Separator | Visual divider between content or controls | Divider, rule, hr |
| toast | Toast | Transient non-blocking message | Snackbar, notification |
| alert | Alert | Persistent in-page status message | Banner alert, callout |
| service-message | Service Message | Site-wide informational banner about temporary status | Site banner, announcement banner, VMA |
| cookie-banner | Cookie Banner | Consent UI for cookie or tracking preferences | Consent banner, consent dialog, cookie consent, cookie notice |
| progress-bar | Progress Bar | Visual indicator of completion or determinate state | Progress indicator |
| spinner | Spinner | Small indeterminate animated indicator, usually inline | Loading spinner, activity indicator, throbber |
| loader | Loader | Page or section-level loading state, often blocking with optional message | Page loader, loading overlay, loading screen, full-page loader |
| badge | Badge | Small read-only status or label indicator | Pill, label |
| chip | Chip | Compact interactive element representing an input, attribute, or filter | Token, tag (interactive) |
| stat | Stat | Single-metric display with value, label, and optional delta | Metric, KPI, stat tile, number |
| rating | Rating | User-facing rating control or display, usually star-based | Star rating, score, stars |
| micro-feedback | Micro Feedback | Lightweight feedback prompt for a single binary or short-tap response | Was this helpful, thumbs up/down, quick feedback, reaction |
| video | Video | Embedded or hosted video | — |
| audio | Audio | Embedded audio player with transport controls | Audio player, podcast player, sound clip |
| image | Image | Static image with semantics (alt, caption) | Picture |
| icon | Icon | Small symbolic graphic | Glyph, symbol |
| carousel | Carousel | Horizontally scrollable sequence of content slides | Slider, slideshow, rotator |
| gallery | Image Gallery | Grid or lightbox collection of images for browsing | Image grid, photo gallery, lightbox |
| map | Map | Embedded geographic map, usually interactive | Map embed, location map |
| calendar | Calendar | View of dates in month/week/day format, often with events | Schedule view, agenda view |
| avatar | Avatar | Circular or rounded image representing a person or entity | Profile picture, user image |
| skeleton | Skeleton | Loading placeholder shape | Shimmer, loader |

### 2.4 Considerations: the accordion architecture

A **consideration** is a topic worth thinking about for a given page type or
component. Considerations are the primary thing the user reads. They are
represented as **large accordions**, each containing:

- A **title** (e.g., "Page title & H1," "Primary CTA placement")
- An **intro paragraph** — short general info text. May be empty in v1; the
  user writes these editorially over time. The build agent should not
  auto-generate this.
- An ordered list of **sub-accordions**.

Each **sub-accordion** is a specific piece of sourced guidance:

- A **one-liner** visible when collapsed (e.g., "WCAG 2.4.6 requires
  headings and labels to describe topic or purpose").
- One or more **phase tags** (e.g., `[ux, accessibility]`). Multiple tags
  are normal and correct.
- A **date** (when this guidance was last updated in the source).
- A **source attribution** (e.g., "W3C / WCAG 2.2," "Nielsen Norman Group").
- A **link** to the external source.
- An expanded **body** — short and substantial. Paragraphs, lists, occasional
  code blocks. No images for v1.

When the user opens a sub-accordion that has both mobile and desktop
considerations, both appear in the body as prose with bold sub-headers
("On mobile" / "On desktop"). Viewport is **not** a filterable tag in v1.

---

## 3. Page structure and interaction model

### 3.1 Main read view

When the user lands on `/page-type/article-page` (or any page-type slug),
they see:

- **Header.** Site title (bestpractice), search input, link to admin queue,
  link to source management.
- **Filter rail** (left on desktop, top accordion on mobile). Phase
  checkboxes, all checked by default. Toggle to filter. Below the phase
  filters, a "Show site-wide considerations" toggle that mixes the
  `site-wide` page's considerations into the current view.
- **Main column.** The page type's label, its definition, then the
  considerations in their authored order, **grouped** by section header.

For Article Page, the groups are:

- **Before you start** — workflow considerations without a spatial location
  (e.g., "Page purpose & audience").
- **Top of page** — considerations for the visible top region (URL,
  eyebrow, title/H1, lead, byline).
- **Body** — considerations for the main content area.
- **End of page** — considerations for the bottom region (related, sharing,
  comments).
- **Behind the scenes** — considerations that aren't visible on the page
  itself (meta description, structured data markup).

Other page types may have different groupings. The build agent should treat
group as a field on each consideration (`group_label` and `group_order`),
not as a hardcoded structure. The user authors group names per page type.

### 3.2 Accordion behavior

- Large accordions are **closed by default**. Click to expand. Multiple can
  be open simultaneously.
- Sub-accordions are **closed by default**. Click to expand. Multiple can
  be open simultaneously.
- Expanded state persists in the URL hash so a deep link works, e.g.
  `/page-type/article-page#h1-and-title.wcag-246`.
- Use native `<details>`/`<summary>` where possible. Style with CSS. Enhance
  with minimal JS only for hash-state and filter-driven hiding.

### 3.3 Filter behavior

- Phase checkboxes are independent toggles. By default, all are on.
- A sub-accordion is **visible** if any of its phase tags is in the active
  set. A sub-accordion with no phase tags is always visible.
- After filtering, if a large accordion has zero visible sub-accordions, the
  large accordion itself becomes **invisible** (collapses out of the page).
  Hide entirely, not greyed out — empty accordions waste screen space.
- Group section headers also hide when all their large accordions are empty.

### 3.4 The "new" indicator

Sub-accordions whose `last_updated` date is within the last **14 days** are
marked **new**. The indicator is visible at the one-liner row so users can
scan without expanding.

Use the blue accent color, applied minimally — a dot, a thin left border, or
a small chip. The design agent chooses the specific treatment. Don't apply
blue to anything else; "new" is the one and only meaning of the accent.

### 3.5 Search

Top-of-page search input. Searches across:

- Large accordion titles
- Sub-accordion one-liners
- Sub-accordion bodies
- Page type labels and synonyms
- Component labels and synonyms
- Phase labels and synonyms

Results page (`/search?q=...`) shows hits grouped by page type or component,
with the matching accordion title and a snippet of context. Click a result
to jump to the relevant page with the matching accordion expanded.

Search is the **only** navigation feature that needs significant JS. Use a
small client-side index for the synonym lookups and fuzzy matching, server-
side full-text for body text. Build agent decides specifics.

### 3.6 Admin: review queue

`/admin/queue` is a separate view, accessed via a link in the main header.

When the ingestion pipeline runs (RSS poll, structured data sync), Groq
scores each new item, assigns suggested phase tags, and writes a one-liner.
These suggestions land in the **review queue** in `pending` status. They do
not appear on the read surface until approved.

The queue shows each pending sub-accordion with:

- The AI-suggested one-liner (editable inline)
- Suggested phase tags (editable inline, can add/remove)
- Suggested association: which large accordion this belongs under (editable
  via dropdown)
- Source name, date, URL
- A longer extract from the source for context
- Three actions: **Approve**, **Edit & approve** (opens a fuller editor),
  **Reject** (deletes the row)

Approved items appear on the read surface with a fresh `last_updated` date,
which means they show the "new" indicator for 14 days.

### 3.7 Admin: source management

`/admin/sources` lists ingestion sources:

- Name, type (RSS, structured-import), URL
- Status (active, paused, error)
- Last collected date
- Item count to date
- Toggle active/paused

Form to add a new source. Minimal UI — this is admin territory, doesn't need
to be pretty, just functional.

### 3.8 Admin: considerations editor

`/admin/considerations/<page-type-slug>` lets the user manage the large
accordion structure for a page type:

- Reorder large accordions by drag (group ordering and within-group order)
- Edit large accordion title and intro paragraph
- Add a new large accordion (with group selection)
- Soft-delete a large accordion

This is the editorial back-office. Used when authoring or restructuring.

---

## 4. Data model

The build agent owns the implementation. This is the conceptual model both
agents should understand.

### 4.1 Tables

**`phases`** — fixed taxonomy table, seeded from the list in §2.1.

- `slug` (PK), `label`, `definition`, `display_order`

**`page_types`** — fixed taxonomy table, seeded from the list in §2.2.

- `slug` (PK), `label`, `definition`, `schema_org_type`, `display_order`

**`components`** — fixed taxonomy table, seeded from the list in §2.3.

- `slug` (PK), `label`, `definition`, `display_order`

**`synonyms`** — flat lookup table for search.

- `id`, `entity_type` (phase/page_type/component), `entity_slug`, `synonym`

**`considerations`** — the large accordions.

- `id`, `parent_type` (page_type or component), `parent_slug`,
  `title`, `intro`, `group_label`, `group_order`, `display_order`,
  `created_at`, `updated_at`

**`sub_considerations`** — the sub-accordions.

- `id`, `consideration_id` (FK), `one_liner`, `body`, `source_name`,
  `source_url`, `source_date`, `status` (pending/approved/rejected),
  `created_at`, `last_updated`, `superseded_by` (FK to another
  sub_consideration, nullable)

**`sub_consideration_phases`** — many-to-many, sub_consideration to phase.

- `sub_consideration_id` (FK), `phase_slug` (FK)

**`sources`** — ingestion sources.

- `id`, `name`, `type` (rss/structured), `url`, `status`, `last_collected`,
  `item_count`, `config_json` (per-source config)

### 4.2 Conventions

- All slugs are kebab-case, URL-safe.
- All datetimes UTC ISO 8601.
- Soft-delete via `status` field where applicable; no hard deletes for
  things the user authored.
- A sub-consideration may have **zero** phase tags. This is valid and means
  "applies to all phases."

### 4.3 Example record (illustrative)

A large accordion for Article Page:

```
consideration {
  id: 42
  parent_type: page_type
  parent_slug: article-page
  title: "Page title & H1"
  intro: ""  # empty in v1
  group_label: "Top of page"
  group_order: 2
  display_order: 3
}
```

One of its sub-accordions:

```
sub_consideration {
  id: 117
  consideration_id: 42
  one_liner: "Match the H1 to the title tag unless SEO demands a longer title"
  body: "The visible H1 and the document <title> are usually the same..."
  source_name: "Nielsen Norman Group"
  source_url: "https://www.nngroup.com/articles/page-titles/"
  source_date: "2024-09-12"
  status: approved
  last_updated: "2026-03-15"
  superseded_by: null
}
sub_consideration_phases: [seo, content, ux]
```

---

## 5. Sources for v1

### 5.1 Structured sources

Imported directly from machine-readable sources (JSON, JSON-LD, or
structured Markdown in a public git repo — no HTML scraping, no auth, no
API keys). Re-synced on a schedule (weekly for fast-moving, on version
bumps for slow specs). The build agent decides how to map source items to
sub-accordions and which large accordion to associate them with — likely
via a per-source configuration that maps source categories to consideration
IDs.

All structured sources change format occasionally. Write mappers
defensively and **log loudly** when a source's shape changes, the same way
AmuseAlot aborts loudly on a bad GitHub token rather than silently
producing empty output.

- **caniuse.com** — JSON database, raw file from
  `raw.githubusercontent.com/Fyrd/caniuse/main/data.json`. Browser support
  data per feature. Map features to relevant component considerations.
  Re-fetch weekly, diff against last copy.
- **MDN browser-compat-data (BCD)** — JSON from
  `github.com/mdn/browser-compat-data` (also published as the
  `@mdn/browser-compat-data` npm package, which is just JSON). More granular
  than caniuse. Re-fetch weekly, diff.
- **WCAG 2.2** — W3C guidelines repo `github.com/w3c/wcag`, success criteria
  available as structured data with stable IDs. Each success criterion
  becomes a sub-accordion tagged with appropriate phases. Slow source —
  re-check on WCAG version bumps, not weekly.
- **Schema.org** — full vocabulary as JSON-LD at
  `schema.org/version/latest/schemaorg-current-https.jsonld`. Extract the
  WebPage subtree. Rarely changes.
- **OWASP** — Top 10 (`github.com/OWASP/Top10`) and Cheat Sheet Series
  (`github.com/OWASP/CheatSheetSeries`), both structured Markdown in public
  repos. Primary-source security guidance. Maps to `backend` and `site-wide`
  security considerations. Slow source — re-check on releases.
- **GOV.UK Design System** — content lives in a public GitHub repo with
  consistent per-component page structure. Ingest from the source repo, not
  the rendered HTML site. Excellent quality, very slow-moving, strong fit
  for component considerations.

### 5.2 RSS sources

Ingested via the same pattern as AmuseAlot's `collect_news.py`: ETag caching,
content-hash dedup, langdetect.

- **web.dev** — `https://web.dev/rss.xml`
- **Nielsen Norman Group** — `https://www.nngroup.com/feed/rss/`
- **The A11y Project** — `https://www.a11yproject.com/feed.xml`
- **Google Search Central** — Google's official search/SEO blog has an RSS
  feed. Primary-source authority for the `seo` phase.

### 5.3 Manual reference sources — NOT ingested

These are high-quality references the **user** consults while authoring
intro paragraphs and reviewing the queue. They are explicitly **not**
pipeline sources: no RSS, no public structured export, no source repo for
the guidance, and/or terms that discourage scraping. The build agent must
**not** attempt to ingest or scrape these. Listing them here so the effort
is not wasted trying.

- **Material Design 3** (`m3.material.io`) — designed site, JS-heavy, no
  guidance export. Manual reference only.
- **Apple Human Interface Guidelines** — no RSS/repo/API, discourages
  scraping, only partial overlap with web. Manual reference only.
- **Baymard Institute** (`baymard.com`) — substantive research is paywalled;
  free RSS is teaser-only. Not pipeline-worthy. Manual reference only (more
  valuable if the user has a subscription, but still not ingestible).

### 5.4 Future sources (not v1)

Out of scope for the first cut, but worth keeping the schema flexible
enough to add: MDN content corpus (`github.com/mdn/content` — large, held
back from v1 to avoid swamping the review queue early; BCD alone is enough
MDN for v1), MDN blog, Smashing Magazine RSS (`smashingmagazine.com/feed/`
— signal varies, optional), A List Apart, Adrian Roselli, Heydon Pickering,
Sara Soueidan, USWDS release notes.

---

## 6. AI scoring and editorial workflow

bestpractice uses Groq + Llama 3.3 for scoring and summarization, matching
AmuseAlot's pattern. The scoring code in `score_news.py` is a useful
reference for retry behavior, rate limiting, and prompt structure.

### 6.1 Scoring pass

For each new source item, the scorer returns:

- A **relevance score** (1–10). Items below a threshold (TBD by build agent,
  start at 4) are auto-rejected.
- **Suggested phase tags** from the 10-phase taxonomy. Zero or more.
- A **suggested large accordion** to associate with — chosen from the
  existing considerations for the source's most likely page type or
  component.
- A **rewritten one-liner** (under 120 characters).
- The **first paragraph of body content**, lightly edited for clarity.

The scoring prompt should make clear:

- The audience: one experienced UX/frontend professional, not a beginner.
- The tone: terse, accurate, no marketing language.
- Bias toward primary sources (specs, standards, research) over commentary.

### 6.2 Editorial gate

The scorer **never publishes directly**. All scored items land in the review
queue with status `pending`. The user approves, edits, or rejects manually.

This is non-negotiable. The whole reason the tool exists is to be more
trustworthy than algorithmic feeds; auto-publish would defeat that.

### 6.3 No auto-overwrite

When new guidance contradicts existing guidance, do **not** auto-overwrite.
The user manually links the old sub-accordion via the `superseded_by` field
when they review the new item. Old sub-accordions with a non-null
`superseded_by` are hidden from the read surface by default but remain in
the database.

---

## 7. Deployment context

Same VPS as AmuseAlot (`root@77.42.40.207`). Same operational patterns.

- **Reverse proxy:** Caddy. Add a new site block for `best.amusealot.com`.
- **Process management:** systemd. Add a new service unit
  `bestpractice.service`. Port 5681 (AmuseAlot is on 5680).
- **Auth:** Caddy basic auth at the proxy layer. Single user. Credentials in
  `/opt/bestpractice/.htpasswd-style` file, generated with `caddy hash-password`.
- **Storage:** SQLite. Single file at `/opt/bestpractice/data/bestpractice.db`.
  Daily backup via cron.
- **Env config:** `/opt/bestpractice/.env`. Same loading pattern as AmuseAlot's
  `run_newsletter.sh` (set -a, source, set +a).
- **Logs:** `/opt/bestpractice/logs/`, rotated daily.
- **Deploy:** scp Python and template files from local machine to VPS, then
  `systemctl restart bestpractice`. PowerShell-friendly (no WSL on the dev
  machine). A `deploy.ps1` is reasonable.

The build agent must produce a `Caddyfile` snippet, a `bestpractice.service`
unit file, and a `deploy.ps1` (or equivalent) as part of the deliverables.

**Network egress.** The ingestion pipeline needs the VPS to reach:
`raw.githubusercontent.com`, `github.com`, `schema.org`, `web.dev`,
`www.nngroup.com`, `www.a11yproject.com`, the Google Search Central blog
host, and `api.groq.com`. AmuseAlot already talks to GitHub and Groq, so
those are proven; the others are new egress. The build agent should verify
reachability as an early step and fail loudly (not silently) if a host is
blocked, consistent with the editorial principle that the user must always
know when collection breaks.

---

## 8. Technical stack

**Backend.** Python 3.12+, Flask, Jinja2, SQLite (`sqlite3` stdlib is fine;
SQLAlchemy is overkill for this scale).

**Frontend.** Server-rendered HTML. **Radix Themes CSS** loaded as a static
stylesheet for design tokens and aesthetic. Vanilla JS for interactions —
no React, no Vue, no Svelte, no build step, no bundler, no npm.

Native HTML where useful: `<details>` and `<summary>` for accordions,
`<dialog>` for modals, `<input type="search">` for search.

For the small number of interactions where native HTML falls short
(dropdown menu, popover, complex select), write per-feature vanilla JS in
small files under `static/js/`. Keep each file under 100 lines. Reach for a
micro-library only if a feature genuinely needs it and the build agent
documents why.

**Icons.** Radix Icons (`@radix-ui/react-icons` has a CDN-friendly SVG
distribution — alternatively, just copy SVG files into `static/icons/`).

**Type.** Inter, self-hosted from `static/fonts/`. Use the variable font
file to keep the asset light.

**AI.** Groq + Llama 3.3 (`llama-3.3-70b-versatile`). Same client pattern
as AmuseAlot.

---

## 9. Editorial principles

These are about *what gets published*, not how it's built. The user enforces
them; both agents should be aware of them because they shape several
decisions.

- **Slow over loud.** Prefer specs, standards, and research-backed sources.
  Avoid hot takes and trend-chasing.
- **Primary over secondary.** A WCAG success criterion beats a blog post
  about WCAG.
- **Short and substantial.** Sub-accordion bodies should be tight. If a
  source needs three paragraphs, summarize in one and link out.
- **Tag honestly.** Don't over-tag for visibility. A consideration that's
  genuinely SEO-only gets only `seo`, not `seo, content, frontend`.
- **Never auto-publish.** Always pass through the editorial gate.
- **Date everything.** The user needs to see when each piece of guidance
  was last updated in its source.

---

## 10. Non-goals

To prevent scope creep, these are explicitly **not** in v1:

- Multiple users, accounts, auth beyond basic auth at the proxy
- Public read access
- Comments, ratings, social features
- Mobile native app
- Dark mode toggle
- Image content (placeholders are fine; no image hosting)
- Real-time collaboration
- Versioning of sub-accordion edits (keep last-write-wins; user is sole
  editor)
- Multi-language support
- Public-facing API
- A newsletter (AmuseAlot already serves that need for a different audience)

---

## 11. What the design agent owns

Visual decisions, typography scale, spacing rhythm, microcopy in UI chrome,
empty-state design, the specific treatment of the "new" indicator, the
mobile adaptation strategy, iconography choices within the Radix Icons set,
how filters visually communicate active state.

The design agent produces a static HTML/CSS prototype of the four key views
described in `DESIGN_HANDOVER.md`. The prototype is the source of truth
for everything visual.

## 12. What the build agent owns

The Flask application, the SQLite schema (in this document's data model
shape), the ingestion pipeline (RSS + structured), the Groq scoring, the
admin queue and source management views, the search index, deployment
artifacts.

The build agent inherits the design prototype and wires it up. The build
agent **does not** redesign — if something in the prototype needs to change
for technical reasons, the build agent flags it for the user, who decides.

---

## 13. Glossary

- **Phase** — a discipline filter (UX, SEO, etc.)
- **Page type** — a kind of page someone builds (article, search results, etc.)
- **Component** — a UI element (button, accordion, etc.)
- **Consideration** — a large accordion within a page type or component
- **Sub-consideration / sub-accordion** — a specific sourced item under a
  consideration
- **Source** — an external feed or dataset bestpractice ingests from
- **Review queue** — admin view where AI-scored items wait for human approval
- **The "new" indicator** — blue accent on sub-accordions updated within 14 days
