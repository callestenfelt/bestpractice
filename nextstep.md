# bestpractice — next steps

Last updated: 2026-05-16 (Session 9 — v3 chrome: sidebar nav + filters drawer + Phosphor icons)

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

## Next session — Session 10 starts here

**Slice C — ingestion + Groq scoring.** First user-facing payoff is
real pending rows in `/admin/queue`. Reference the §6 ingestion
pattern in `PROJECT.md`; the working pattern lives in
AmuseAlot/musemaniac's `collect_news.py` (ETag caching, content-hash
dedup, langdetect) + `score_news.py` (retry/rate-limit, prompt
shape). Local path per Session 1's reference memory:
`E:\_dev\musemaniac`.

Now that the sidebar nav surfaces every slug with the "new" dot
computed from `last_updated`, the natural visual payoff of Slice C
is the dot lighting up as ingestion approves items — gives the user
a real signal for "what changed this week" across the whole
taxonomy.

Order of operations for Slice C:
1. **`collect.py`** — iterate active `sources` rows, fetch feeds
   with ETag/Last-Modified caching, hash-dedup against
   `sub_considerations.body`, write candidates into
   `sub_considerations` with `status='pending'`,
   `relevance_score=NULL`.
2. **`score.py`** — Groq-score pending rows 1–10 against the page
   type / component routing guidance from `PROJECT.md`, write back
   to `relevance_score`. Items below a threshold (e.g. 4) stay
   pending but won't bubble to the top of the queue.
3. **`/admin/queue` write paths** — approve / reject / edit-and-
   approve POST handlers. The `<dialog>` from `BUILD_NOTES.md` §2.3
   is the prototype contract for edit-and-approve; build it as a
   dedicated modal rather than reusing the filters drawer.

### Tech-debt nudges parked from earlier sessions
- VPS Python is 3.10.12; `PROJECT.md` §8 calls for 3.12+. No 3.12-
  only syntax used yet; flag if Slice C reaches for it.
- Daily SQLite backup cron + log rotation on the VPS — last
  unchecked item from Session 2's deploy-prep list. Ingestion makes
  this more urgent (DB is no longer purely append-on-deploy).
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
