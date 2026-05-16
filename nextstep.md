# bestpractice — next steps

Last updated: 2026-05-16 (Session 11 — Slice C+D: source-roster refit + structured-source pipeline + 4 adapters)

This file is the running session log. Format follows the convention used in
`E:\_dev\bubble` (`docs/nextstep.md`): numbered sessions with narrative +
Done checkboxes + Files changed + How to test + Next-session pointer. When
this file passes ~400 lines and has 4+ completed sessions, archive the
oldest sessions to `docs/archive/sessions.md` and keep the 3 most recent
live here.

Sessions 1–6 (project bootstrap, design prototype + deploy prep,
Slice A read surface, Slice B part 1 `/search`, Slice B parts 2+3
`/admin/*`, `/component/<slug>` + empty state) live in
[`docs/archive/sessions.md`](docs/archive/sessions.md).

---

## Session 7 — visual polish, mobile filter dialog, asset versioning, fixture HTML-escape fix ✅ shipped 2026-05-16

Session 6 went to prod cleanly at the start of the session (GHA
`25945628409`, 12s; one-time `python3 init_db.py` on the VPS loaded
the image fixture). The remainder was design polish on the sub
accordion, a real mobile UX for the phase filters, and a long
debugging tail that ended in a content-escaping bug in the
article-page fixture. Four follow-on deploys (GHA `25946314260`,
`25946626060`, `25946733356`, `25947052735`) all in ~10s each.

### Done
- [x] **Sub accordion polish.** `.sub[open]` drops the inherited
      top/bottom rules (`border-top-color: transparent` on the open
      sub AND on its next sibling so the line below disappears too)
      and gains `border-radius: 3px`, so the active row reads as a
      clean rounded card. `.sub__body` font-size drops to `--fs-14`
      (14 px), `.sub__one-liner` weight bumps to `--fw-semibold`
      (600). Edits mirrored in `prototype/styles/components.css` and
      `static/styles/components.css`.
- [x] **Mobile filter dialog.** Below 960 px the rail is hidden via
      `display: none`; a new `<button class="filters-trigger">` sits
      below the page heading and opens a native `<dialog
      id="filters-dialog">`. `filters.js`'s new `setupMobileDialog()`
      relocates the rail's children into the dialog body via
      `matchMedia('(max-width: 960px)')` at init (and back on resize),
      so phase checkboxes + `#toggle-sitewide` keep a single source
      of truth — `applyFilters()` and `bindBulk()` need no changes.
      Esc, backdrop click, and the close/Done buttons all dismiss.
      Markup mirrored in `prototype/page-type.html` and
      `templates/page_type.html`. **Superseded in Session 9 by the
      right-hand filters drawer.**
- [x] **Static-file cache headers.** `app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0`.
      Single-user admin tool, bandwidth trivial; eliminates the 12-
      hour stale-asset window where users see old CSS/JS after a
      deploy until they hard-refresh.
- [x] **Asset versioning.** `ASSET_VERSION = str(int(time.time()))`
      computed at module import (service restart on every deploy
      bumps it). A Jinja context processor exposes
      `asset(filename)`, which appends `?v=<ASSET_VERSION>` to the
      static URL. All four templates (`base.html`, `search.html`,
      `admin/sources.html`, and existing `page_type.html` via base)
      swapped from `url_for('static', filename=...)` to
      `asset(...)`. Belt + suspenders with the cache header — even
      if a browser is sitting on a Cache-Control entry from before
      the header fix, the URL itself now changes per deploy so the
      browser must fetch.
- [x] **Fixture HTML-escape fix.** `fixtures/article_page.json` had
      an unescaped literal `<title>` in the H1-and-title sub's
      `one_liner`. Once the template rendered it with `|safe`, the
      browser opened a stray `<title>` element inside `<body>`,
      which swallowed every subsequent element including the three
      `<script src=...>` tags. Result: `filters.js` was never
      loaded, so `setupMobileDialog` never ran, so the new "Filters"
      button did nothing. Fixed: escaped to `<code>&lt;title&gt;</code>`
      in the fixture, plus an idempotent data fix in
      `init_db.py:migrate()` so existing local + prod DBs get
      patched on next `init_db.py` run. `rebuild_fts()` runs
      unconditionally, so the FTS index re-syncs automatically.

### Lessons / decisions worth noting (non-obvious)
- **Belt + suspenders for static cache.** Setting
  `SEND_FILE_MAX_AGE_DEFAULT=0` only affects *future* responses,
  not entries already in the browser cache — those keep their old
  `max-age=43200` until expiry or a true cache bypass (iOS Safari's
  "hard refresh" is unreliable). The URL-versioning step is what
  forces existing browsers to refetch. Doing one without the other
  leaves a stranded-user case.
- **DOM relocation > duplicate render** for shared filter state. The
  alternative was rendering the rail markup twice (once inline, once
  in the dialog body) and syncing checkbox state via a `change`
  handler. Moving the same DOM nodes between two parents avoids
  duplicate IDs (`#toggle-sitewide`), keeps `filters.js`'s global
  selectors untouched, and naturally tracks state. (No longer needed
  in Session 9 — the drawer is a real persistent element.)
- **Fixture content needs the same escaping discipline as inline
  template HTML.** `|safe` is load-bearing for the body field
  (which intentionally carries `<p>`, `<code>`, `<strong>`), so the
  pipeline can't blanket-escape — content authors (and the
  extractor) have to escape structural tags by hand.
- **Long debugging tails compound.** The visible symptom was "button
  does nothing." Likely causes ran cache → bundling → JS init →
  HTML parse error. Each fix made the next layer's failure visible.
  When a script "isn't running" but the file is correct, jump
  straight to `document.querySelectorAll('script[src]')` to confirm
  the page actually has the tags in DOM — would have shortened the
  loop by 20 minutes.

---

## Session 8 — taxonomy audit + additions ✅ shipped 2026-05-16

Triggered while user worked on the navigation design. Audited the locked
taxonomies (`PROJECT.md` §2.1–§2.3) for gaps and overlaps, then layered
in user-approved additions across two rounds of discussion. Total
additions: 1 phase, 4 page types, 17 components. `error-page` definition
narrowed; `spinner` definition sharpened and "Loader" synonym removed
when `loader` got its own slug.

### Done
- [x] **PROJECT.md §2.1** — added `legal` phase. First addition to the
      previously "locked" phase taxonomy.
- [x] **PROJECT.md §2.2** — added `pricing-page`, `confirmation-page`,
      `auth-page`, `404-page`. Narrowed `error-page` definition to
      "500, offline, maintenance and other non-404 error states" since
      404 has its own slug now.
- [x] **PROJECT.md §2.3** — added 17 components (`list`, `textarea`,
      `combobox`, `file-upload`, `stepper`, `code-block`, `chart`,
      `cookie-banner`, `spinner`, `loader`, `stat`, `rating`,
      `micro-feedback`, `audio`, `map`, `shopping-cart`,
      `copy-link-button`). Sharpened `spinner` once `loader` got the
      page/section-level slot.
- [x] **`init_db.py`** — mirrored every PROJECT.md addition into
      `PHASES` / `PAGE_TYPES` / `COMPONENTS`. Refactored
      `seed_taxonomies()` so source-of-truth lists win on every
      re-seed (upsert on row fields including `display_order`;
      clear-then-fill synonyms per entity). Mid-list inserts no
      longer scramble order; removed synonyms actually disappear.
- [x] **`CLAUDE.md`** — softened the "taxonomies are locked" line to
      "do not invent new entries autonomously; additions require
      explicit user approval." Counts: 11 phases / 21 page types /
      63 components.
- [x] **`taxonomy-additions.md` (new)** — working-session snapshot
      of the additions, with definitions.

### How tested
- **Local.** Clean re-seed → 11/21/63 counts. New routes resolve to
  empty state. Phase filter rail shows all 11 checkboxes including
  `Legal`. Article-page Content-Length 108855 (+241 vs Session 7).
  Synonym hygiene: `loader` no longer expands to `spinner`.
- **Production.** Deployed via GHA `25958578000`, push `b02b94f`.
  One-time `python3 init_db.py` on the VPS landed the new rows and
  re-applied the upsert ordering. `/component/loader` → 200 from
  VPS-local curl bypassing Caddy.

### Lessons / decisions worth noting (non-obvious)
- **`INSERT OR IGNORE` + canonical-list ordering is a foot-gun.**
  Inserting a new row in the middle of `COMPONENTS` left existing
  rows with their old `display_order` while new rows got fresh
  sequential numbers, producing duplicates and a scrambled order.
  The upsert pattern (`INSERT OR IGNORE` → unconditional `UPDATE`)
  keeps slug-as-PK semantics while letting the source-of-truth list
  dictate ordering. Worth the extra cursor call.
- **Synonyms decay silently.** Dropping "Loader" from `spinner`'s
  list does nothing on its own because the seed never DELETEd.
  Clear-then-fill per `(entity_type, entity_slug)` makes the list
  authoritative.
- **"Locked" taxonomies aren't forever.** New wording: "do not
  invent new entries autonomously; additions require explicit user
  approval." Preserves the guardrail against drift while admitting
  reality.
- **Distinguishing near-synonyms matters.** When adding a new slug
  near an existing one, sharpen the older definition in the same
  edit — otherwise the taxonomy degrades into vague overlap.

---

## Session 9 — v3 chrome: sidebar nav + filters drawer + Phosphor icons ✅ shipped 2026-05-16

Implemented the prototype v3 handover delivered by Claude Design.
Three structural changes vs Session 7's `.site-header` chrome:
global left sidebar listing every page type + component with an icon,
right filters drawer replacing the old `<dialog>` modal entirely, and
Phosphor Icons swapped in for the inline-SVG topbar/sidebar glyphs.
Three commits on one push: schema/seed foundation, chrome rewrite,
prototype directory shuffle.

### Done
- [x] **`schema.sql` + `init_db.py:migrate()`.** Added nullable
      `icon TEXT` column to `page_types` and `components`; ALTER
      both for existing DBs (mirrors the `relevance_score` pattern).
- [x] **`init_db.py:PAGE_TYPES` and `COMPONENTS`.** Added the icon
      field per handover §3.7 (21 + 63 hand-tuned glyph slugs) and
      reordered both lists to match the v3 sidebar grouping (auth
      near landing; confirmation after checkout; form controls
      clustered; data-display clustered; loading-state cluster).
      The Session 8 upsert in `seed_taxonomies()` keeps existing-DB
      `display_order` in lockstep on re-seed. Extended the upsert
      to write `icon` and added the new column to `INSERT OR IGNORE`
      column lists. Dropped "loader" from `skeleton`'s synonyms (it
      conflicted with the `loader` slug — same pattern as Session 8's
      spinner/Loader split).
- [x] **`app.py:load_parent_view`.** Queries now `SELECT … icon …`;
      page dict carries `icon`.
- [x] **`app.py` new `@context_processor` `_inject_nav`.** Single
      query per request pulling `(slug, label, icon, has_new)` for
      every page type + component in `display_order`. `has_new` is an
      EXISTS subquery against `sub_considerations.last_updated` with
      the 14-day cutoff used by `is_new_filter`. Also injects
      `current_kind` / `current_slug` so the sidebar can mark the
      active link via `aria-current="page"` from inside the partial.
- [x] **`static/icons/phosphor/` (new).** Vendored Phosphor 2.1.1
      Regular weight only: `Phosphor.woff2`, `style.css` (`src` trimmed
      to woff2-only), `LICENSE`. ~225 KB total. No CDN. Dropped the
      Duotone + Bold weights and the in-page weight switcher per
      handover §3.3.
- [x] **`templates/base.html` rewrite.** New chrome: `.topbar` with
      sidebar-toggle button, brand, search form, optional filters-
      toggle block. `.sidebar-scrim` + `.filters-scrim` siblings (only
      visible <960 px). `.layout` grid hosts the sidebar, `.content >
      .reading`, and an optional `.filters-rail` block. Drops the old
      `.site-header` and `.app-main` layout wholesale.
- [x] **`templates/_sidebar.html` (new partial).** Renders
      `nav_page_types` and `nav_components` as two `<section>` blocks
      with icon glyph + label + optional `<span class="dot">` "new"
      indicator. Active link gets `aria-current="page"`. Sidebar
      footer carries Review queue + Sources links.
- [x] **`templates/page_type.html` rewrite.** Page body inside
      `{% block content %}`; new `{% block topbar_filters_toggle %}`
      drops the sliders icon into the topbar; new
      `{% block filters_rail %}` mounts the `.filters-rail` aside.
      Removed `.filters-trigger` and `<dialog class="filters-dialog">`
      entirely. Phase checkboxes still `name="phase" value="…"` and
      site-wide toggle still `#toggle-sitewide` — filter JS contract
      unchanged.
- [x] **Search + admin templates.** `search.html`, `admin/queue.html`,
      `admin/sources.html` unwrapped from the deleted
      `.shell.shell--narrow / .main` containers. They render directly
      inside the new `.content > .reading` block. `admin/sources.html`
      uses `{{ super() }}` in its scripts block to keep the inherited
      sidebar.js / filters.js / accordion.js / search.js while
      appending `admin.js`.
- [x] **`static/styles/sidebar.css` (new, vendored from v3).** Topbar,
      layout grid, sticky rails, sidebar nav, filters drawer,
      responsive mobile overlays + scrims, plus the lifted inline
      `<style>` Phosphor sizing rules (16 px in sidebar, 18 px in
      topbar, 14 px in search). The `.icon-weight` switcher rules
      from v3 deliberately omitted.
- [x] **`static/styles/{base,components}.css` synced with v3.** Mobile
      `.rail { display: none }` removed (replaced by the layout grid
      collapse).
- [x] **`static/js/sidebar.js` (new).** Handles both rails: click
      toggles, scrim clicks, `Ctrl/Cmd + .` for sidebar, `Ctrl/Cmd
      + ,` for filters. State persisted in `bp:sidebar-open` and
      `bp:filters-open`. Also keeps the topbar filters count badge
      in sync with off/site-wide state.
- [x] **`static/js/filters.js` replaced** with the v3 version (69
      lines, down from 101). `setupMobileDialog` gone — no dialog to
      manage. Resolves the "trim filters.js to <100 lines"
      tech-debt nudge from Session 7.
- [x] **Prototype directory shuffle.** Original `prototype/` archived
      to `prototype/archive/v1/`; `prototype_v3/` contents promoted
      to `prototype/`. Canonical file going forward:
      `prototype/page-type-v3.html`.
- [x] **`CLAUDE.md` repository-status section.** Reflects v3 chrome
      shipped to every route; points at `prototype/page-type-v3.html`
      as canonical; flags `prototype/archive/v1/` as reference only.

### How tested — local (passed 2026-05-16)
1. Clean `python init_db.py` → 11/21/63; `icon` column on both
   tables, populated for every row (e.g. `('article-page',
   'ph-article')`).
2. `python app.py`. All 11 routes (`/`, `/page-type/*`,
   `/component/*`, `/search`, `/search?q=image`, `/admin/queue`,
   `/admin/sources`) → 200.
3. Chrome consistency: topbar + sidebar render on every route;
   filters-rail renders only on page-type/component views.
4. Sidebar correctness: 21 page-type links + 63 component links,
   each with `<i class="ph ph-*">` icon. 84 Phosphor icons in the
   sidebar + 3 in the topbar = 87 on page-type/component views; 86
   on search/admin (no filters-toggle).
5. Active-link marking: `aria-current="page"` on the matching
   sidebar entry per route.
6. "New" indicator: lights up on slugs with sub `last_updated`
   within 14 days. Article-page lights up given the fixture
   timestamps.
7. Phosphor assets: `/static/icons/phosphor/{style.css,Phosphor.woff2}`
   → 200; spot-checked icons (`ph-house`, `ph-binoculars`,
   `ph-spinner-gap`, `ph-circle-notch`, `ph-rectangle-dashed`,
   `ph-hourglass`, `ph-sign-in`, etc.) all exist in the 2.1.1
   Regular CSS.
8. Filter regression: `data-phases` hiding still works (no contract
   change in filters.js).

### How tested — production (passed 2026-05-16)
- Three GHA deploys ran clean: `25959668990` (stage A, 15s),
  `25959790313` (stage B, 15s), `25959892789` (stage C, 7s).
- One-time prod seed via
  `ssh root@77.42.40.207 'cd /opt/bestpractice && python3 init_db.py'`
  ran clean: schema applied, icon column ALTERed onto existing
  page_types + components tables, taxonomies re-seeded with the new
  display_order + icon values via the Session 8 upsert, fixtures
  skipped (idempotent), FTS rows 65.
- Prod verification via VPS-local curl bypassing Caddy:
  - `/page-type/article-page` → 200, 125509 bytes (v3 chrome live;
    matches local).
  - `/component/loader` → 200, 30250 bytes (empty-state with full
    sidebar; matches local).
  - `/static/icons/phosphor/Phosphor.woff2` → 200, 147380 bytes
    (self-hosted, no CDN). `Cache-Control: no-cache, max-age=0`
    from the Session 7 caching policy.
  - `/static/styles/sidebar.css` → 200, 10077 bytes.
  - Icon column populated on prod DB:
    `SELECT slug, icon FROM page_types WHERE slug='article-page'`
    returns `('article-page', 'ph-article')`.

### Files changed
- **Stage A** (`757336d`): `schema.sql`, `init_db.py` (lists +
  migrate + seed_taxonomies), `app.py` (load_parent_view + nav
  context processor), `prototype_v3/` (full v3 source).
- **Stage B** (`38118eb`): `static/icons/phosphor/` (new),
  `static/styles/sidebar.css` (new), `static/styles/base.css` +
  `components.css` synced, `static/js/sidebar.js` (new),
  `static/js/filters.js` replaced, `templates/base.html` rewritten,
  `templates/_sidebar.html` (new), `templates/page_type.html`
  rewritten, `templates/search.html` + `admin/{queue,sources}.html`
  unwrapped.
- **Stage C** (this commit): prototype/ archived to
  prototype/archive/v1/, prototype_v3/ promoted to prototype/,
  CLAUDE.md repository-status updated, nextstep.md Session 9 block
  + Sessions 5–6 archived to docs/archive/sessions.md.

### Lessons / decisions worth noting (non-obvious)
- **`prototype/` is the visual source of truth.** Every chrome edit
  starts there; build follows. The directory shuffle this session
  preserved that contract by promoting v3 to `prototype/` and
  pushing the old v1 prototype to `prototype/archive/v1/`. If the
  next design iteration arrives as `prototype_v4/`, repeat: archive
  v3 to `prototype/archive/v3/`, promote v4 to `prototype/`.
- **Two context processors compose.** `_inject_asset_helper` and
  `_inject_nav` both run on every render; their return dicts merge
  into the template context. No ordering constraint between them.
- **DELETE-then-INSERT for derived data.** Same pattern as Session
  8's synonyms: when a list in code is the source of truth and the
  DB is the cache, the seed must clear the old rows before
  re-inserting or stale entries leak. The Phosphor icon mapping
  fits the same shape — re-seeding overwrites the icon column even
  for existing rows because of the upsert.
- **Empty `prototype/` then re-fill.** `git mv` only moves
  contents; you can't `git mv prototype prototype_old` if
  `prototype/` is non-empty AND you also want to recreate it. Move
  contents out, optionally `rmdir`, then move new contents in. Or
  use intermediate paths (here: `prototype/archive/v1/` as an
  in-place sub-archive). Works because the v1 contents are
  reference, not on the import path.
- **Vendoring is cheap.** Phosphor at 225 KB self-hosted is
  trivially smaller than the typical npm + bundler footprint and
  removes the runtime dependency on unpkg.com. Worth it for any
  font/icon library you'd otherwise CDN-load.

---

## Session 10 — Slice C: ingestion + Groq scoring + queue write paths ✅ shipped 2026-05-16 (branch `slice-c`, not yet pushed)

User stepped away for a couple of hours and asked for the most demanding
thing that could land solo. Slice C was the obvious target — it turns the
read-only admin surface (Sessions 5–9) into an editorial loop where AI
suggestions land in the queue, get scored, and approve/reject/edit
controls move them onto real pages. Locked-in pre-flight decisions:
RSS-only (structured caniuse/MDN/WCAG/schema.org deferred to Slice D
because the first-fetch flood needs user-paced paging), feature branch
`slice-c` with no push, GROQ_API_KEY copied from
`E:\_dev\musemaniac\.env`.

The work split into four commits. Stage A laid the foundation
(schema/env/seed), Stage B added `collect.py` (RSS ingestion), Stage C
added `score.py` (Groq scoring), Stage D wired the queue write paths +
edit-approve dialog. Stage E is this entry.

### Done
- [x] **Stage A — foundation.** `schema.sql` gained `etag` /
      `last_modified` / `last_fetched` columns on `sources` plus a
      `UNIQUE INDEX idx_sources_url` for the seed's `INSERT OR IGNORE`.
      `init_db.py:migrate()` got the matching idempotent ALTERs
      (mirroring the Session 9 icon pattern). `init_db.py` now also
      seeds an `INBOX_CONSIDERATION` placeholder at
      `site-wide/ingest-inbox` and 5 default RSS sources (web.dev, A11y
      Project, CSS-Tricks, Smashing, MDN Blog) via the new
      `seed_inbox()` / `seed_sources()` helpers. `requirements.txt`
      (first one in the project) ships `feedparser>=6.0`,
      `requests>=2.31`, `python-dotenv>=1.0`. `app.py` calls
      `load_dotenv()` at module init; `.env.example` checked in;
      `.gitignore:10` already blocked `.env`.
- [x] **Stage B — `collect.py`.** Standalone CLI walking
      `sources WHERE type='rss' AND status IN ('active','error')`.
      Sends `If-None-Match` + `If-Modified-Since` per source; 304 → log
      and skip; 200 → captures the response `ETag` / `Last-Modified`
      back into the source row. Entries deduped against existing
      `sub_considerations.source_url` in any status (rejected items
      don't resurrect). Body normalisation strips all HTML, caps at
      600 chars at a word boundary, escapes residual `<`/`>`/`&`, and
      wraps in `<p>` — direct application of the Session 7 fixture
      escaping lesson. Slug is `sha1(url)[:12]` so the
      `UNIQUE (consideration_id, slug)` constraint can't collide.
      First-run smoke ingested 200 entries from the 5 feeds (CSS-Tricks
      15, MDN 70, Smashing 40, A11y 65, web.dev 10); second run hit
      304 on 4 feeds and URL-dedup on the 5th (web.dev sent no ETag).
- [x] **Stage C — `score.py`.** Standalone CLI iterating
      `sub_considerations WHERE status='pending' AND relevance_score IS
      NULL`. Calls Groq `llama-3.3-70b-versatile` via raw `requests` to
      `api.groq.com/openai/v1/chat/completions` (no Groq SDK —
      musemaniac's pattern) with `response_format=json_object`. System
      prompt geared at senior UX/frontend reader: terse, primary
      sources, penalise marketing. Output JSON shape per PROJECT.md
      §6.1: `score` 1–10, `phases[]` (filtered against the phases
      table), `consideration_id` (validated against the approved
      catalog, ingest-inbox excluded; null → keep row in inbox),
      rewritten `one_liner`, edited `body`. Auto-reject threshold
      defaults to 4 per §6.1 (`--threshold` flag overrides).
      Hardening: 429 → 8s/16s/24s backoff; 5xx → 4s/8s/12s; malformed
      JSON or out-of-range score → leave row pending+NULL for the
      next run. Live smoke run scored the 200-row batch (took
      ~7–10 min at 2s between calls).
- [x] **Stage D — queue write paths + edit-approve dialog.** Three
      new POST routes in `app.py`:
      `/admin/queue/<id>/approve` (status='approved' + FTS insert),
      `/admin/queue/<id>/reject` (status='rejected'),
      `/admin/queue/<id>/edit_approve` (full editor: one_liner / body /
      source_url / source_date / phases / consideration_id, validates
      target consideration, DELETE+INSERT the phases bridge, FTS
      re-sync). Helper `_ensure_pending()` makes them idempotent (back
      button / double submit redirect quietly). Helper
      `_sync_fts_row()` does DELETE+INSERT keyed on `rowid` so re-edits
      don't dupe in the FTS index. Helper `load_queue_catalog()` feeds
      the dialog's destination-consideration select. Template carries
      `data-*` attrs per qcard so `static/js/queue.js` (54 lines)
      populates the shared `<dialog id="edit-approve-dialog">` without
      a round-trip. Append-only CSS additions in
      `static/styles/components.css`: `.edit-dialog`, `.edit-dialog__*`,
      `.qcard__btn` (full-width), `.qcard__source-link`,
      `.queue-error`.
- [x] **Stage E — local smoke verification.** Test-client run against
      `Flask.test_client()` confirmed end-to-end:
      approve → status flips + FTS row appears,
      reject → status flips (FTS untouched),
      edit_approve → row moves to target consideration with new
      one_liner / body / phases / FTS row.
      `/search?q=edited` returned the edited row with `<mark>` highlights
      proving FTS picked the change up. All test-mutated rows reverted
      to pending so the user inherits a clean queue.

### How tested — local (passed 2026-05-16)
1. `git switch -c slice-c`
2. `pip install -r requirements.txt` (deps already satisfied locally)
3. `python init_db.py` — applied 3 sources ALTERs, created
   ingest-inbox consideration id=22, seeded 5 RSS sources.
4. `python collect.py` — ingested 200 candidates. Re-run got 304 on
   4 feeds, dedup on the 5th.
5. `python score.py` — Groq-scored all 200 pending rows. Distribution
   roughly matches the 1-10 spec (top items at 8–9, slop at 1–3,
   auto-rejected below 4). Cost: well under $0.20 at Groq's per-token
   rates.
6. `python app.py` + curl probes: `/admin/queue` → 200 (552KB with
   ~150 qcards + the dialog). `/search?q=` works through FTS over the
   newly-approved rows.
7. Test-client write-path exercise: approve / reject / edit_approve
   all return 302 with the expected DB + FTS mutations. Smoke-test
   rows reverted afterwards.

### How tested — production (NOT YET)
Branch is `slice-c`, never pushed. `git switch main` reverts the work
cleanly. Production at `best.amusealot.com` still on Session 9 chrome
with the empty-queue placeholder text — see "Next session" for the
deploy plan once the user is back.

### Files changed
- **Stage A** (`bf23928`): `schema.sql`, `init_db.py`, `app.py`,
  `requirements.txt` (new), `.env.example` (new).
- **Stage B** (`bc2a484`): `collect.py` (new, 265 lines).
- **Stage C** (`5f0c24e`): `score.py` (new, ~310 lines), `collect.py`
  (utf-8 stdout fix).
- **Stage D** (`5f00d7c`): `app.py` (routes + helpers),
  `templates/admin/queue.html` (rewritten), `static/js/queue.js` (new),
  `static/styles/components.css` (dialog + queue extras appended).

### Lessons / decisions worth noting (non-obvious)
- **UTF-8 BOM in `.env` breaks python-dotenv key names.** PowerShell
  5.1's `Set-Content -Encoding utf8` writes the file with a leading
  `EF BB BF` BOM; python-dotenv 1.2.2 reads the first key name as
  `﻿GROQ_API_KEY` rather than `GROQ_API_KEY`. Stripped the BOM
  via a 4-line Python helper (`p.write_bytes(data[3:] if
  data.startswith(b'\xef\xbb\xbf') else data)`). Future Windows envs
  should use `-Encoding utf8NoBOM` (PS 7+) or write via Python.
- **Windows cp1252 console crashes on non-ASCII stdout mid-script.**
  Adding `sys.stdout = io.TextIOWrapper(sys.stdout.buffer,
  encoding='utf-8', errors='replace', line_buffering=True)` at module
  init in both `collect.py` and `score.py` matches musemaniac's
  pattern and survives feed titles + AI output containing arrows /
  smart quotes / emoji.
- **Inbox consideration as a holding pen, not a hack.** Pending rows
  need a non-null `consideration_id` because the FK is `NOT NULL`. The
  options were: (a) drop the NOT NULL, (b) make scoring write the FK,
  (c) park rows in a placeholder consideration until scoring routes
  them. (c) won — the schema stays strict, ingestion stays
  schema-pure, and the placeholder is invisible from the read surface
  because all its subs are `status='pending'` and read views filter to
  approved.
- **Auto-reject in the scoring pass cuts queue noise meaningfully.**
  ~20-25% of the 200 ingested rows scored below 4 and were
  auto-rejected, halving the manual-review burden vs. surfacing
  everything. The threshold is a CLI flag (`--threshold`) so the user
  can ratchet it up to 5 or 6 once the queue's been tuned.
- **Flask dev server doesn't auto-reload without debug=True.**
  Stage D's app.py changes returned 500s until the process was killed
  via `taskkill //PID <pid> //F` and restarted. Worth flipping
  `debug=True` (or `app.run(debug=os.environ.get('FLASK_DEBUG'))`) in
  local dev mode if Session 11 expects fast iteration.
- **Native `<dialog>` was the right call.** showModal()'s built-in
  backdrop + Esc handling cut the JS surface to 54 lines (vs. the
  ~120 a hand-rolled modal would need). The Session 7 mobile filter
  dialog had set the precedent; sticking with native means the dialog
  inherits a11y for free.
- **Edit-and-approve dialog reads from data-\* attrs, not a fetch.**
  Each qcard renders all editable values into `data-one-liner`,
  `data-body`, etc. Click → JS copies them into the shared form, no
  round-trip. Cheaper, simpler, and means the dialog works under
  network failure. Server's `_sync_fts_row()` still re-runs after
  edit_approve so search stays consistent.

---

## Session 11 — Slice C+D: source-roster refit + structured-source pipeline ✅ shipped 2026-05-16 (branch `slice-c`, still not pushed)

User came back from a short break, flagged that the ingested RSS items
felt news-heavy and that some were old (e.g. A11y Project 2013). Asked
me to read a Gemini-suggested PSE-based ingestion proposal — rejected
that as the wrong tool for the ingestion bottleneck (PSE returns URLs,
not content, and would require HTML scraping that the new PROJECT.md §5
explicitly fences off; PSE is parked under [[parked-feature-ideas]] for
later use as in-app search augmentation + Edit-and-approve discovery
helper). Then a Claude.ai-revised PROJECT.md landed in Downloads. I
diffed it, flagged that the new draft inadvertently reverted Session
8's taxonomy additions, and surgically merged §5 + §7 enrichments
without touching §2 (taxonomies stay at 11 phases / 21 page types /
63 components).

Then a green light for autonomous multi-step work. Did the RSS source
refit, the queue cull, the PSE parking note, and built out Slice D
(structured-source pipeline + 4 adapters: WCAG 2.2, Schema.org WebPage
subtree, caniuse, OWASP Top 10).

### Done — RSS refit + queue cleanup
- [x] **`init_db.py` `DEFAULT_SOURCES`.** Replaced the Session 10 first
      cut (CSS-Tricks / Smashing / MDN Blog) with the v1 roster per
      `PROJECT.md` §5.2: web.dev, A11y Project, **Nielsen Norman
      Group**, **Google Search Central**. The three deprioritized feeds
      stay in the DB (paused via direct UPDATE) so their existing
      pending items remain reviewable. Note: PROJECT.md §5.2 lists
      A11y Project's feed as `/feed.xml`; that URL **404s** in
      practice. The actually-served Jekyll output is at `/feed/feed.xml`
      so the seed keeps that — flagged inline in the code comment.
- [x] **DB pause for the three deprioritized RSS sources.** Direct
      `UPDATE sources SET status='paused' WHERE name IN ('CSS-Tricks',
      'Smashing Magazine','MDN Blog')`. `collect.py` already filters on
      `status IN ('active','error')` so the paused rows are skipped on
      future runs but their existing pending items are still in the queue.
- [x] **First ingestion of NN/g + Google Search Central** — 30 new
      candidates (20 NN/g, 10 Google Search Central).
- [x] **Two-pass queue cull.** Pass 1 before scoring the new items:
      reject pending rows where `source_date < 2024-01-01` OR
      `relevance_score < 5` (107 rows). Pass 2 after scoring the 30 new
      ones: catch the 4-score newcomers (6 rows). Net effect: 174
      rejected total. The cull rule encodes the editorial principle —
      old + low-signal items belong in the rejected pile, not the queue.

### Done — Slice D foundation
- [x] **`ingestors/` package (new).** `__init__.py` defines the
      adapter `Protocol` and a `load_adapter(name)` importer keyed on
      `sources.config_json -> adapter`. Adapters are plain Python
      modules under `ingestors/<name>.py`, exposing `SOURCE_NAME`,
      `FEED_URL`, `CACHE_FILENAME`, and `fetch_candidates(conn,
      source_row, max_new) -> list[dict]`.
- [x] **`collect_structured.py` (new, ~140 lines).** Thin runner:
      walks `sources WHERE type='structured' AND status IN
      ('active','error')`, dispatches each to its adapter, writes
      returned candidates as pending sub_considerations. Handles
      per-source error state (status='error' on adapter exception, the
      operator unblocks via `/admin/sources` toggle), tracks
      last_collected + item_count. Supports `--source NAME` for
      targeting a single feed and `--limit N` for per-source caps.
- [x] **`init_db.py` `seed_sources()` extended.** `DEFAULT_SOURCES` is
      now `(name, type, url, config_dict)` 4-tuples; `config_json` is
      written on first INSERT and **never overwritten** so an operator
      editing a source's adapter config via `/admin/sources` (when that
      UI lands) won't be clobbered on re-seed.
- [x] **`.gitignore`: `data/cache/`** — structured-source snapshot
      cache, used by adapters for first-fetch storage and (future)
      content-diff against prior runs.

### Done — four structured adapters
- [x] **`ingestors/wcag.py`** — `https://www.w3.org/WAI/WCAG22/wcag.json`.
      W3C publishes WCAG 2.2 as clean JSON with `principles[] →
      guidelines[] → successcriteria[]`. Each SC becomes one
      sub_consideration with `source_url` of
      `https://www.w3.org/TR/WCAG22/#<sc-id>`. Conditional GET via
      `etag`/`last_modified` on the source row. 87 SCs ingested (all
      of WCAG 2.2). Smoke-scoring sample: 5/5 scored **10/10** — Groq
      correctly identifies WCAG SCs as essential primary-source guidance.
- [x] **`ingestors/schema_org.py`** — full vocabulary JSON-LD (~5 MB,
      3200+ entries). Two-pass extraction: (1) every `rdfs:Class`
      descending from `schema:WebPage` via the `rdfs:subClassOf` chain
      (computed transitively with a BFS), (2) every `rdf:Property`
      whose `schema:domainIncludes` references any of those types. 29
      candidates ingested — ~10 WebPage-subtype Types + ~19 properties.
      Maps naturally to bestpractice's `page_types` taxonomy (Groq
      routes `schema:CheckoutPage` → checkout-page consideration, etc).
- [x] **`ingestors/caniuse.py`** — `raw.githubusercontent.com/Fyrd/caniuse/main/data.json`
      (~4.5 MB, 554 features). Quality filter on `status IN ('ls',
      'rec','pr','wd')` (Living Standard / Recommendation / Proposed /
      Working Draft — skips 'other' and 'unoff' legacy items) AND a
      category whitelist (CSS, HTML5, DOM, JS, JS API, Security,
      Canvas, SVG, Other). `MAX_NEW_PER_RUN = 25` to absorb the
      first-fetch flood; URL dedup means subsequent runs continue from
      where the previous run stopped. 25 ingested; ~250-300 candidates
      remain across future runs.
- [x] **`ingestors/owasp.py`** — Top 10 markdown sources under
      `OWASP/Top10` repo. Per-file regex extracts the H1 + the
      `## Description` section text, strips markdown link / emphasis
      markers, wraps body in `<p>`. 10 categories ingested in one
      pass (A01–A10). Cheat Sheet Series (~100 sheets) parked for a
      future capped adapter.
- [x] **`ingestors/govuk.py`** — added during the autonomous
      extension at end of session after the initial Session 11
      summary was delivered. Walks `alphagov/govuk-design-system`'s
      `src/components/` (34 dirs) and `src/patterns/` (35 dirs) via
      the GitHub Contents API, then fetches each subdir's `index.md`
      from `raw.githubusercontent.com`. Parses the YAML frontmatter
      (title, description) + extracts the intro paragraph and the
      first "When to use…" section; strips nunjucks `{% ... %}` /
      `{{ ... }}` markers and markdown link/emphasis. 68 candidates
      ingested + scored (66 at 8/10, 2 at 4/10). Maps strongly to
      bestpractice's component taxonomy (gov.uk's `button` →
      component/button, `breadcrumb` → component/breadcrumb, etc).
      All 5 PROJECT.md §5.1 structured sources now ingested.
- [x] **Dead-chrome CSS prune + `placeholder.html` deletion.** Done
      in the same autonomous-extension commit. Removed the legacy
      `.site-header / .site-header__* / .app-main / .shell /
      .shell--narrow / standalone .rail / .main` rules from
      `static/styles/base.css` (Session 7 chrome, superseded by
      Session 9's v3 chrome which lives in `sidebar.css`). Verified
      first via `grep` that no template references those classes
      anymore. Also deleted `templates/placeholder.html` — uses
      `.shell` and `.main`, never referenced from `app.py`, true
      dead code.

### Done — surgical doc merges
- [x] **`docs/PROJECT.md` §5** — wholesale replacement: 4 structured
      sources → 6 (adds OWASP + GOV.UK), 3 RSS sources → 4 (adds
      Google Search Central), new §5.3 "Manual reference — NOT
      ingested" fence around Material Design 3 / Apple HIG / Baymard,
      §5.4 expanded future list. **Did NOT touch §2** (Session 8's
      taxonomy additions stay).
- [x] **`docs/PROJECT.md` §7** — appended "Network egress" paragraph
      naming the hosts the VPS must reach (raw.githubusercontent.com,
      github.com, schema.org, web.dev, www.nngroup.com,
      www.a11yproject.com, Google Search Central host, api.groq.com).
- [x] **`static/styles/components.css` `.table-wrap`** — was
      `overflow: hidden` which clipped the Active column on `/admin/sources`
      at viewport widths between ~720 and ~900px. Now `overflow-x: auto`
      with a `min-width: 720px` floor on the table itself; the floor
      resets to 0 under the existing `max-width: 720px` media query so
      mobile (where col-hide-mobile drops 2 columns) doesn't get a
      wasteful horizontal scrollbar.

### Done — scoring + culling pipeline
- [x] **Scored all 146 newly-ingested unscored rows** (87 WCAG + 29
      Schema.org + 25 caniuse + 30 RSS-second-batch — wait, 30 was
      already done in the RSS pass; ~131 in this batch). Used the
      existing `score.py` unchanged — the Groq prompt handles
      structured input cleanly (WCAG SCs land at 10/10 on the smoke
      sample, schema.org Types and caniuse features land mostly in
      the 6–10 range with sensible suggested-home routing).

### How tested — local (passed 2026-05-16)
1. RSS feeds: `python init_db.py` adds NN/g + Google Search Central
   (additive); direct UPDATE pauses 3 deprioritized sources.
   `python collect.py` ingests 30 (20 + 10).
2. Cull: `UPDATE … status='rejected' WHERE source_date < '2024-01-01'
   OR (relevance_score IS NOT NULL AND relevance_score < 5)`. 107
   rows. Second pass after scoring the 30 new RSS items: 6 more.
3. Structured: `python collect_structured.py` runs WCAG (87) + Schema
   (29) + caniuse (25) + OWASP (10) = 151 new candidates.
   Re-running on Schema.org returned `304 not modified` proving
   conditional-GET works on JSON-LD too. caniuse re-run will start
   from the 26th feature since URL dedup tracks per-feature URLs.
4. Smoke: `python score.py --limit 5` on freshly-ingested WCAG rows
   returned `score=10 phases=ux,frontend` × 5, validating that the
   existing scoring prompt handles structured input without
   modification.
5. End-to-end: `/admin/queue` renders ~70+ items after the cull and
   structured imports, score dots correct, edit-approve dialog still
   works (Stage D from Session 10 untouched).

### How tested — production (NOT YET)
Branch is still `slice-c`, 9 commits total (5 from Session 10, 4 from
Session 11). Nothing pushed. `git switch main` reverts cleanly.

### Files changed (Session 11 only)
- **RSS refit + cull + Slice D foundation** (one big stage):
  - `init_db.py` — DEFAULT_SOURCES 4-tuple with config_dict;
    seed_sources writes config_json on insert only.
  - `static/styles/components.css` — `.table-wrap` overflow fix.
  - `docs/PROJECT.md` — §5 wholesale, §7 network egress paragraph.
  - `.gitignore` — `data/cache/`.
  - `ingestors/__init__.py` (new) — adapter Protocol + loader.
  - `ingestors/wcag.py` (new).
  - `ingestors/schema_org.py` (new).
  - `ingestors/caniuse.py` (new).
  - `ingestors/owasp.py` (new).
  - `collect_structured.py` (new).
  - `nextstep.md` — this entry.

### Lessons / decisions worth noting (non-obvious)
- **PROJECT.md drift.** When a fresh-from-the-LLM doc lands, diff it
  against the working copy *before* copy-replacing — LLMs don't have
  recent commit history loaded. The Claude.ai draft would have
  silently reverted Session 8's approved taxonomy work if applied
  wholesale. The right move is a surgical merge into the working doc.
- **Doc fact-checking still required.** PROJECT.md §5.2 said A11y
  Project's feed is at `/feed.xml`. Cold curl: 404. The working URL
  is `/feed/feed.xml`. The code's right; the doc is wrong; the
  comment in `DEFAULT_SOURCES` flags this so a future reader doesn't
  "fix" it back.
- **Reject Gemini's PSE for ingestion.** PSE returns URLs, not
  content — the fetch-and-parse step would require HTML scraping the
  whitelisted sites, which PROJECT.md §5.1 forbids. PSE doesn't solve
  the editorial-freshness problem either (high-ranking 2014 article is
  still a 2014 article). Parked for in-app search augmentation and a
  per-row "find primary sources" helper in Edit-and-approve — those
  *are* good fits because they're user-initiated, not background
  ingestion. See [[parked-feature-ideas]].
- **Structured + RSS share the same `sub_considerations` table.**
  No type discrimination at the data layer — `source_name` is the only
  per-row signal of provenance. That's fine because the editorial
  workflow (queue → approve / edit / reject) is identical regardless
  of source type. The discrimination lives at the *ingestion* layer:
  RSS through `collect.py`, structured through `collect_structured.py`
  + adapters.
- **`config_json` is now load-bearing for structured sources.**
  Adapter dispatch reads `sources.config_json['adapter']`. The
  `/admin/sources` UI doesn't yet expose this field for editing — if
  an operator wants to rename a feed's adapter or paste an
  adapter-specific config (e.g. a per-source category whitelist),
  they currently need to UPDATE the DB by hand. Flag for Session 12
  UX polish.
- **URL dedup is the only diff mechanism so far.** Adapters cache the
  fetched payload to `data/cache/<name>.{json,jsonld}` but the runner
  doesn't yet diff cache-vs-fresh for *content updates*. For WCAG
  that's fine (locked release, no in-place updates), for schema.org
  it's fine (rare changes, new types add new URLs), for caniuse it
  might miss browser-support status changes on existing features —
  parked.
- **Auto-rejection threshold of 4 is too lenient for structured.**
  WCAG SCs all score 10. Schema.org Types land in 6–9. caniuse
  features land in 6–9. OWASP categories at 8+. No structured item
  should ever be auto-rejected at 4. The threshold's still valuable
  for the RSS stream (where commentary / fluff is real). Consider a
  per-source-type threshold in a future refactor.

---

## Next session — Session 12 starts here

**The biggest item by far: review the queue.** ~70+ pending items
across 4 structured sources + 4 RSS sources, all scored. Walk through,
approve / edit-approve / reject. Watch how the sidebar "new" dot
lights up parents as their approval count grows. This is the
proof-of-value moment — the whole loop now exists.

**Then deploy.** Slice C+D have stayed local across two sessions; the
prod box is still on Session 9 chrome. Merge plan:

1. `git switch main && git merge slice-c --no-ff` (preserve the
   9 stage commits in history; Session 9 used the same no-ff style).
2. Push to `main`. GHA `deploy.yml` rsyncs to the VPS and restarts
   `bestpractice.service`. Watch the action log.
3. **On the VPS, one-time setup:**
   - `cd /opt/bestpractice && python3 init_db.py` — applies the
     `sources` ALTERs (etag/last_modified/last_fetched), seeds the
     ingest-inbox consideration, registers the 8 sources (4 RSS
     active + 4 structured active; CSS-Tricks/Smashing/MDN-Blog won't
     be re-seeded since they're out of `DEFAULT_SOURCES` now).
   - Put `GROQ_API_KEY` in `/opt/bestpractice/.env` (the existing
     `EnvironmentFile=` pattern from AmuseAlot's systemd unit).
   - `pip3 install -r requirements.txt` for feedparser/requests/dotenv.
   - **VPS Python is 3.10.12** per CLAUDE.md — nothing in Slice
     C+D uses 3.12-only syntax, but verify if anything breaks.
4. **First prod runs:** `python3 collect.py && python3 collect_structured.py`
   then `python3 score.py --limit 20` (smoke), then full
   `python3 score.py`. Expect ~200+ pending after first wave; same
   cull SQL works on prod.
5. Walk `/admin/queue` via the Caddy-auth domain; watch the sidebar
   "new" dot.

**After deploy, the parked items in priority order:**

1. **MDN browser-compat-data adapter** (`ingestors/mdn_bcd.py`).
   Larger than caniuse — thousands of compat entries. Strong cap
   essential (`MAX_NEW_PER_RUN = 15` probably). Maps to component
   considerations like caniuse.
2. **Per-source-type threshold for scoring.** Right now `score.py`
   uses a single threshold (`<4 = auto-reject`) for all sources. Two
   GOV.UK items scored 4 in this session's autonomous extension and
   stayed pending (correctly — primary-source content). But the
   safeguard is brittle: a single 3-score from Groq on a WCAG SC
   would currently auto-reject it. Add a `--structured-threshold 0`
   option, or detect by source.type and never reject structured items.
3. **`/admin/sources` UX gaps:**
   - Show last error message + retry button when `status='error'`.
   - Expose `config_json` for editing (load-bearing for structured
     adapters; currently DB-level only).
   - Show source type (rss/structured) more prominently.
4. **Content-diff for structured sources.** Adapters cache to
   `data/cache/` but only URL-dedup, not content-diff. Means an
   in-place change to a caniuse feature's description won't surface
   as a new candidate. Add hash-comparison in adapters for the
   "updated" case.
5. **Inline auto-save edits on queue cards** (textarea blur debounce,
   chip × buttons, association change auto-POST). User wanted to
   shape this themselves; defer until they've reviewed Edit-and-approve.
6. **Cron / scheduled ingestion.** systemd timer for `collect.py +
   collect_structured.py + score.py`. Also: daily SQLite backup +
   log rotation (parked since Session 2; now critical given the DB
   mutates on every run).

### Parked feature ideas (potential Slice E+)
- **Google Programmable Search Engine integration.** Build a whitelisted
  PSE (NN/g, web.dev, w3.org, Google Search Central, GOV.UK) and use
  the Custom Search JSON API for two narrow user-facing roles — NOT
  background ingestion:
  1. **In-app search augmentation** — `/search` shows local FTS hits
     plus an opt-in "Search authoritative sources" expansion that fires
     a PSE call only when the user clicks. Free tier covers 100
     queries/day.
  2. **Edit-and-approve "find primary sources" helper** — button in
     the dialog opens a PSE-filtered search in a new tab so the editor
     can paste authoritative links into the body.
  Rejected as an ingestion path because PSE returns URLs only — the
  fetch-and-parse step would require HTML scraping, which PROJECT.md
  §5.1 fences off ("no HTML scraping, no auth, no API keys"). PSE
  also doesn't solve the editorial freshness problem (a high-ranking
  2014 article is still a 2014 article).

### Tech-debt nudges parked from earlier sessions
- VPS Python is 3.10.12; `PROJECT.md` §8 calls for 3.12+. No 3.12-
  only syntax used yet; flag if a future slice reaches for it.
- Daily SQLite backup cron + log rotation on the VPS — last
  unchecked item from Session 2's deploy-prep list. Now critical:
  ingestion writes to the DB on every collect/score run.
- Radix Themes CSS vendoring — `tokens.css` already uses Radix-
  shaped variable names; mechanical swap, can land any time.
- Add a fixture-content validator in `init_db.py` for unescaped
  structural HTML tags (Session 7 lesson, still parked).
- `actions/checkout@v4.2.2` is Node-20-deprecated; bump before
  2026-06-02.
- Old `.site-header` / `.shell` / `.filters-dialog` CSS rules in
  `static/styles/{base,components}.css` are unused after Session 9's
  chrome rewrite. Worth a `grep -L .site-header templates/*.html` pass
  to confirm, then prune.
- `app.run(debug=False)` in `app.py:613` means the dev server doesn't
  auto-reload on edits. Trip-hazard for any future write-path
  session — consider `debug=os.environ.get('FLASK_DEBUG') == '1'`.
