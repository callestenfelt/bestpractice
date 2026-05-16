# bestpractice — next steps

Last updated: 2026-05-16 (Session 8 — taxonomy audit + additions: legal phase, 4 page types, 17 components)

This file is the running session log. Format follows the convention used in
`E:\_dev\bubble` (`docs/nextstep.md`): numbered sessions with narrative +
Done checkboxes + Files changed + How to test + Next-session pointer. When
this file passes ~400 lines and has 4+ completed sessions, archive the
oldest sessions to `docs/archive/sessions.md` and keep the 3 most recent
live here.

Sessions 1–4 (project bootstrap, design prototype + deploy prep,
Slice A read surface, Slice B part 1 `/search`) live in
[`docs/archive/sessions.md`](docs/archive/sessions.md).

---


## Session 5 — Slice B parts 2 + 3: /admin/queue + /admin/sources ✅ shipped 2026-05-16

The two admin shells from the Session 4 punch list. `/admin/queue` is a
**read-only** view of `sub_considerations WHERE status='pending'` —
approve/reject/edit POST handlers defer to Slice C, when ingestion
actually creates pending rows. `/admin/sources` is the full CRUD shell:
list, add (RSS only — name + URL), and per-row toggle (active ↔ paused;
error → active for operator unblocking).

Pushed in two commits with one deploy gap so the prod migration could
run between them. Locally verified by inserting a synthetic pending row
+ a synthetic source through the admin POST routes, then deleting both.

### Done
- [x] `schema.sql` — nullable `relevance_score INTEGER` on
      `sub_considerations` for Groq's 1–10 score on AI-suggested items.
- [x] `init_db.py` — new `migrate()` step compares `PRAGMA
      table_info(sub_considerations)` against expected columns and
      `ALTER`s anything missing. `CREATE TABLE IF NOT EXISTS` doesn't
      touch existing tables, so any future column add must be wired
      through `migrate()`. Idempotent — re-running adds nothing.
- [x] `app.py` — `_format_relative()` formats an ISO timestamp as
      "just now", "12m ago", "2h ago", "yesterday", "3d ago", or a
      bare ISO date past 7 days. `load_queue_view()` joins pending
      subs to parent + phases, computes `pending_count` /
      `approved_week` (`last_updated >= now-7d`) / `rejected_count`,
      and a `last_sync` string from `MAX(sources.last_collected) WHERE
      status='active'`.
- [x] `app.py` — `/admin/sources` GET lists rows ordered (active first,
      then alpha). POST `/admin/sources` adds an RSS source with
      `status='active'` (validates name + http(s) URL; bad input
      redirects with `?error=…` echoed by the template). POST
      `/admin/sources/<id>/toggle` flips `active` ↔ `paused`; `error`
      promotes to `active` (operator unblocking the feed).
- [x] `templates/admin/queue.html` — extends `base.html`. Empty state
      points operators at `/admin/sources`. When pending rows exist:
      `qcard` per item with source meta (name + dot + date + score
      strip via Jinja macro), one-liner as static `<p>` (no
      textarea), phase chips (no remove ×), "Suggested home" as a
      static breadcrumb of `parent_label · group_label · cons_title`,
      body extract. The aside is empty for now (sr-only message
      announcing approve/reject controls land in Slice C).
- [x] `templates/admin/sources.html` — extends `base.html`. Table per
      `BUILD_NOTES.md` §2.4 (status dots green/amber/red are the
      approved blue-only exception). Per-row toggle is its own
      `<form method="post" data-auto-submit>` wrapping the prototype's
      `.toggle` checkbox; `<noscript>` falls back to a Save button.
      Add-source form is RSS-only per `BUILD_NOTES.md` §2.4
      (structured needs `config_json`, deferred).
- [x] `static/js/admin.js` (3 lines) — auto-submits any
      `form[data-auto-submit]` on change. Loaded only by
      `templates/admin/sources.html`'s `block scripts` override (not
      every page).

### Files changed
- `schema.sql` — added `relevance_score INTEGER` (nullable)
- `init_db.py` — added `migrate()` for idempotent column adds
- `app.py` — `_format_relative`, `load_queue_view`, three new admin
  routes (queue read; sources GET/POST/toggle); replaced two
  placeholders
- `templates/admin/queue.html` (new)
- `templates/admin/sources.html` (new)
- `static/js/admin.js` (new, 3 lines)
- `nextstep.md` — Session 5 block (this entry); sessions 1–2 archived
  to `docs/archive/sessions.md`
- `docs/archive/sessions.md` (new) — historical Session 1 + 2 blocks

### How to test — local (passed 2026-05-16)
1. `python init_db.py` (twice) → second run reports
   `(skip) article-page already has 16 considerations` and `FTS rows: 59`.
   Verify column exists:
   `sqlite3 data/bestpractice.db 'PRAGMA table_info(sub_considerations)'`
   includes `relevance_score`.
2. `python app.py`.
3. `curl -sI /admin/queue` → 200, ~2.7 KB empty state. Body shows
   `0 pending · 0 approved this week · 0 rejected · Last sync: never`.
4. Insert a pending row by hand (1-line Python via sqlite3), reload,
   confirm `qcard` renders with score strip + chips + breadcrumb.
5. `curl -sI /admin/sources` → 200, "No sources yet" empty state.
6. `curl -X POST /admin/sources -d 'name=web.dev&url=https://web.dev/rss.xml'`
   → 302; reload `/admin/sources` shows the row.
7. Bad inputs (`name=Foo` alone, or `url=ftp://x`) redirect to
   `?error=…` and the template echoes the message.
8. `curl -X POST /admin/sources/<id>/toggle` flips the DB column;
   reload shows status flip. Toggle on a 9999 id → 404.
9. Regression: `/page-type/article-page` Content-Length still 107695,
   `/search?q=image` still 200.

### How tested — production (passed 2026-05-16)
- Push 1 (queue + relevance_score migration) deployed via GHA
  `25944598945` in ~10s, success.
- Push 2 (sources + nextstep + archive) deployed via GHA `25944916410`
  in ~10s, success.
- `ssh root@77.42.40.207 'cd /opt/bestpractice && python3 init_db.py'`
  added the `relevance_score` column to the prod DB. Output: `(skip)
  article-page already has 16 considerations`, `FTS rows: 59`. Idempotent
  — the migration isn't re-run on subsequent invocations.
- Prod verification from the VPS:
  `curl -sI http://localhost:5681/admin/queue` → `HTTP/1.1 200 OK`
  (`Server: Werkzeug/3.1.5 Python/3.10.12`); `/admin/sources` → 200.
- Sibling regression held: amusealot.com 200, bubblesdontcry.com 200,
  staging.bubblesdontcry.com 401, best.amusealot.com 401 — all
  unchanged from Session 4.

### Out of scope (parked — Session 6 starts here)
- `/admin/queue` write paths: approve / reject / edit-and-approve.
  These need pending rows to manipulate, which need ingestion.
- `/admin/considerations/<slug>` — large-accordion editor.
- The "Edit & approve" `<dialog>` from `BUILD_NOTES.md` §2.3.

### Lessons / decisions worth noting (non-obvious)
- **`migrate()` is the new home for column adds.** SQLite's `CREATE
  TABLE IF NOT EXISTS` won't apply changes to an existing table. Any
  future `schema.sql` column needs a parallel ALTER in
  `init_db.py:migrate()`. Pattern: read `PRAGMA table_info(<table>)`,
  diff against expected names, ALTER what's missing. Cheap to call
  every run.
- **No Flask `flash()`.** Adding flash would force a `secret_key` and
  signed session cookies for a single-user admin behind Caddy basic
  auth — not worth it. Errors round-trip through `?error=…` query
  string instead, echoed by the template's `{% if error %}` block.
  Idempotent and bookmarkable.
- **`error` source status promotes to `active` on toggle.** The
  prototype only models active ↔ paused, but `sources.status` allows
  `error`. When operators toggle an errored source, the intent is
  "unblock and try again" — flipping to `active` is the useful
  default. Toggle-from-error → paused would just hide the symptom.
- **`data-auto-submit` is the no-JS fallback contract.** The toggle
  form works without JS via the `<noscript>` Save button. With JS
  loaded, `static/js/admin.js` (3 lines) submits on change. Same form
  HTML in both cases — degrades cleanly.

---

## Session 6 — /component/<slug> + empty state ✅ shipped 2026-05-16

Two cleanups from Session 5's punch list: mount `/component/<slug>` by
generalising the read-view to accept either parent type, and render a
friendly empty state instead of a near-blank page for the 14 page
types and 44 components that don't have considerations yet. Seeded
`image` with 3 considerations / 6 sub-considerations from primary
sources (WHATWG, WCAG, web.dev, MDN, caniuse) so at least one
component route renders non-empty.

### Done
- [x] `app.py` — `load_page_type_view(slug)` renamed and generalised
      to `load_parent_view(parent_type, parent_slug)`; returns
      `(page, parent_kind_label, phases, groups)`. The `page` value
      is a plain dict (`{slug, label, definition, schema_org_type}`)
      so the same template handles both page types and components
      uniformly; `schema_org_type` is None for components. Site-wide
      layering still triggers off `is_sitewide_self`, but now applies
      to components too — site-wide considerations layer onto a
      `/component/<slug>` view exactly as they do onto a page type.
- [x] `app.py` — `/component/<slug>` route added (5 lines). Passes
      `parent_kind='Component'` to the template. The existing
      `/page-type/<slug>` route stays unchanged in URL shape; both
      routes pass `is_self_sitewide` so the template can suppress the
      `hidden` attribute when the user is directly viewing the
      site-wide bucket.
- [x] `templates/page_type.html` — eyebrow swapped from hardcoded
      "Page type" to `{{ parent_kind | default('Page type') }}`. New
      empty-state block renders above the group loop when there are
      no visible groups (i.e. nothing but site-wide), pointing the
      user at the site-wide toggle. Site-wide self-view
      (`/page-type/site-wide`) drops the `hidden` attribute on its
      own group AND suppresses the empty state — previously this
      route showed an always-hidden group with no way to reveal it.
- [x] `fixtures/image_component.json` (new, ~5 KB) — 1 group
      (`image-essentials`), 3 considerations (alt text, responsive
      delivery, stability & format), 6 sub-considerations. Sources:
      WCAG 2.2 SC 1.1.1, WHATWG HTML Living Standard, web.dev
      (responsive images + CLS guide), MDN (`<img> loading`),
      caniuse (AVIF). `last_updated` stamped 2026-05-16 / -10 / -08 /
      -04-30 / -04-22 so the "new" indicator lights up on 4 of 6 subs
      for ~a week, decays naturally after.
- [x] `init_db.py` — `load_article_page_fixture()` replaced by
      generic `load_fixture(conn, parent_type, parent_slug, path)`.
      Driven by a module-level `FIXTURES` list (currently 2 entries:
      article-page + image). Idempotent per `(parent_type,
      parent_slug)`; the article-page fixture continues to populate
      the shared site-wide bucket (group_slug='site-wide' →
      parent_slug='site-wide') without affecting the image component
      check.
- [x] `templates/search.html` — added `{% elif group.kind ==
      'component' %}` branch building `url_for('component',
      slug=...) ~ '#' ~ cons.sub`. Component hits previously fell
      through to `href="#"` (regression that would have surfaced the
      first time a component had searchable content; caught
      end-to-end here by `?q=avif`).

### Files changed
- `app.py` — `load_parent_view`, `/component/<slug>` route,
  `is_self_sitewide` template var
- `templates/page_type.html` — dynamic eyebrow, empty-state block,
  site-wide self-view fix
- `templates/search.html` — component href branch
- `init_db.py` — `FIXTURES` list, generic `load_fixture()`
- `fixtures/image_component.json` (new)
- `nextstep.md` — Session 6 block (this entry)

### How to test — local (passed 2026-05-16)
1. `python init_db.py` (clean DB) → final line `FTS rows: 65` (was 59
   in Session 5; +6 from the image component). Re-running prints
   `(skip) page_type/article-page already has 16 considerations` and
   `(skip) component/image already has 3 considerations`.
2. `python app.py`.
3. `/page-type/article-page` Content-Length **107706** (was 107695
   in Sessions 3–5; +11 bytes from the new conditional template
   block — content unchanged).
4. `/component/image` 200, Content-Length 25130. DOM contains 3
   image considerations + the 2 site-wide considerations (Colour
   contrast, Keyboard navigation) layered as a trailing hidden
   group. Sub IDs match the deep-link contract: e.g.
   `alt-text.wcag-111-informative`.
5. `/component/header` 200, Content-Length 12283 — empty-state body
   renders ("No considerations curated for this component yet…").
6. `/page-type/start-page` 200, Content-Length 12318 — same
   empty-state body, eyebrow reads "Page type".
7. `/component/nonexistent` 404 (parent slug check still firing).
8. `/page-type/site-wide` — empty-state count 0; site-wide group
   renders **without** `hidden`. Considerations visible: Colour
   contrast, Keyboard navigation.
9. `/search?q=avif` → single result, link is
   `/component/image#stability-format.modern-formats` (not `#`).
10. `/search?q=image` → 13 results split across article-page + image
    component; component links resolve correctly.
11. `/search?q=alt+text` → still 200, unchanged.

### Out of scope (parked — Session 7 / Slice C)
- Slice C ingestion + Groq scoring (`collect.py`, `score.py`). First
  pending rows in `/admin/queue` come from here.
- `/admin/queue` write paths (approve / reject / edit-and-approve).
- `/admin/considerations/<slug>` large-accordion editor.
- More component fixtures beyond `image`. The shape is locked
  (same JSON schema as article-page minus the site-wide group); add
  more by dropping a JSON file in `fixtures/` and one tuple in
  `FIXTURES`.
- Production deploy of this session. Untested on the VPS — push to
  `main` triggers GHA; no DB migration is required (no schema
  change), but the image-component fixture needs to load. The
  generic `load_fixture()` runs automatically on next `python3
  init_db.py`; deciding whether to re-run that on the VPS is the
  first step of Session 7.

### Lessons / decisions worth noting (non-obvious)
- **`page` is a dict, not a sqlite3.Row.** Refactoring the view to
  handle both parent kinds meant the template can't assume a
  `Row` shape (components have no `schema_org_type` column). Passing
  a normalised dict avoids template-time `KeyError` and keeps the
  template DRY across the two routes.
- **Site-wide layering applies to components too.** PROJECT.md §2.2
  describes site-wide as "considerations that apply across all
  pages." Reading that strictly, components aren't pages. Read as
  intent: cross-cutting concerns (alt text, contrast, keyboard) are
  *more* relevant on a component view than less. Layered on.
- **`/page-type/site-wide` self-view was always broken.** It rendered
  with the site-wide group's `hidden` attribute set and no UI to
  reveal it. Predated this session, surfaced here because the new
  empty-state block made the bad output more visible. Fixed via an
  `is_self_sitewide` flag through to the template.
- **Search template's `href="#"` fall-through was latent.**
  Pre-Session 6 there were no component hits to expose it. Caught
  immediately on first `?q=avif` curl. Reminder: when adding a new
  parent kind, grep templates for every `parent_type` / `kind` branch
  before declaring done.
- **`{% set %}` inside `{% if %}` does escape the conditional in
  Jinja2.** The page-type branch's href propagating to the `<a>` tag
  is what made me trust the existing pattern; the same pattern now
  carries the component branch.

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
      `templates/page_type.html`.
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

### Files changed
- `app.py` — `SEND_FILE_MAX_AGE_DEFAULT=0`, `ASSET_VERSION`,
  `_inject_asset_helper` context processor, `import time`
- `init_db.py` — `migrate()` data fix for unescaped `<title>`
- `fixtures/article_page.json` — `<title>` → `<code>&lt;title&gt;</code>`
- `templates/base.html`, `templates/search.html`,
  `templates/admin/sources.html` — `url_for('static', filename=…)`
  → `asset(…)`
- `templates/page_type.html` — filter trigger button + dialog
  shell, dynamic eyebrow already in Session 6
- `prototype/page-type.html` — same filter trigger + dialog markup
  (visual-source-of-truth parity)
- `prototype/styles/{base,components}.css` and
  `static/styles/{base,components}.css` — `.rail { display: none }`
  on mobile, sub-accordion polish, `.filters-trigger`/`.filters-dialog`
  styles
- `prototype/js/filters.js` and `static/js/filters.js` —
  `setupMobileDialog()`, tightened `bindBulk()`, 101 lines
- `nextstep.md`, `docs/archive/sessions.md` — Session 7 block + S3
  archived

### How tested
- **Local.** `python init_db.py` → migrate logs no errors;
  `data/bestpractice.db` row for slug `match` has the escaped
  `one_liner`. `python app.py`; `curl
  /page-type/article-page` Content-Length 108614 (+908 bytes over
  Session 6 from the new button + dialog shell + `?v=` query
  strings); page HTML now includes
  `/static/js/filters.js?v=<timestamp>` for every asset. Filter
  trigger button visible only ≤960 px; `<dialog>` shell empty until
  JS init relocates rail children on mobile.
- **Production.** Four GHA deploys, each ~10s. One-time
  `ssh root@77.42.40.207 'cd /opt/bestpractice && python3 init_db.py'`
  after the last deploy applied the migrate data fix; verified via
  `sqlite3` (well, `python3 -c …sqlite3…` since the VPS doesn't have
  the `sqlite3` CLI): the row now reads the escaped form. Prod
  page-type HTML serves versioned URLs; `Cache-Control: no-cache,
  max-age=0` confirmed on `/static/js/filters.js`. User confirmed
  the mobile filter button now opens the dialog.

### Out of scope (parked — Session 8 / Slice C)
- All Slice C work (ingestion + Groq scoring + write paths). See
  Next-session pointer below.
- Tightening `filters.js` below 100 lines per `PROJECT.md`'s
  per-feature JS guideline. Currently 101. Mechanical refactor when
  it next gets edited.
- A fixture-content validator: refuse to seed if any `one_liner` or
  `body` contains an unescaped structural tag (`<script`, `<title`,
  `<style`, `<head`, `<body`, `<html`, `<iframe`). Two minutes to
  add to `init_db.py` and would have caught the bug at seed time
  rather than via user-reported "button does nothing".
- The `actions/checkout@v4.2.2` Node-20 deprecation notice from
  GHA. Forced to Node 24 on 2026-06-02; bump to a Node-24-aware
  version (`actions/checkout@v5` or later) any time before then.

### Lessons / decisions worth noting (non-obvious)
- **Belt + suspenders for static cache.** Setting
  `SEND_FILE_MAX_AGE_DEFAULT=0` only affects *future* responses,
  not entries already in the browser cache — those keep their old
  `max-age=43200` until expiry or a true cache bypass (iOS Safari's
  "hard refresh" is unreliable). The URL-versioning step is what
  forces existing browsers to refetch. Doing one without the other
  leaves a stranded-user case.
- **`<dialog>`'s click-target trick for backdrop dismiss.** A click
  on the backdrop has `e.target === dialog`; a click on the dialog's
  inner content has `e.target` somewhere in the descendants. So
  `if (e.target !== dialog) return; …getBoundingClientRect bounds
  check…` reliably distinguishes them without coordinate math
  alone.
- **DOM relocation > duplicate render** for shared filter state. The
  alternative was rendering the rail markup twice (once inline, once
  in the dialog body) and syncing checkbox state via a `change`
  handler. Moving the same DOM nodes between two parents avoids
  duplicate IDs (`#toggle-sitewide`), keeps `filters.js`'s global
  selectors untouched, and naturally tracks state.
- **`{% set %}` inside `{% if %}` propagates in Jinja2.** Same
  pattern was already working for the page-type branch of the
  search href; the elif for component just slotted in. (Re-noted
  from Session 6 because it was the cause of a five-minute false
  panic during this session's CSS work too.)
- **Fixture content needs the same escaping discipline as inline
  template HTML.** `|safe` is load-bearing for the body field
  (which intentionally carries `<p>`, `<code>`, `<strong>`), so the
  pipeline can't blanket-escape — content authors (and the
  extractor) have to escape structural tags by hand. Adding the
  validator above closes the loop.
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
- [x] **PROJECT.md §2.1** — added `legal` phase ("Privacy, terms,
      consent, accessibility statements, and other regulatory
      considerations"). First addition to the previously "locked"
      phase taxonomy.
- [x] **PROJECT.md §2.2** — added `pricing-page`, `confirmation-page`,
      `auth-page`, `404-page`. Narrowed `error-page` definition to
      "500, offline, maintenance and other non-404 error states" since
      404 has its own slug now.
- [x] **PROJECT.md §2.3** — added 17 components:
      `list`, `textarea`, `combobox`, `file-upload`, `stepper`,
      `code-block`, `chart`, `cookie-banner`, `spinner`, `loader`,
      `stat`, `rating`, `micro-feedback`, `audio`, `map`,
      `shopping-cart`, `copy-link-button`. Positioned by cluster
      (form-input, data-display, feedback, loading, media) to match
      existing §2.3 ordering. Sharpened `spinner` to "Small
      indeterminate animated indicator, usually inline" once `loader`
      got the page/section-level slot.
- [x] **`init_db.py`** — mirrored every PROJECT.md addition into
      `PHASES` / `PAGE_TYPES` / `COMPONENTS`. Also refactored
      `seed_taxonomies()`:
      - After `INSERT OR IGNORE`, run an `UPDATE` on `label`,
        `definition`, `display_order` (and `schema_org_type` for
        page-types). Source-of-truth lists now win on every re-seed;
        mid-list inserts no longer scramble `display_order` on
        existing DBs.
      - Synonyms now `DELETE FROM synonyms WHERE entity_type=? AND
        entity_slug=?` before re-inserting, so removed synonyms
        (e.g. dropping "Loader" off `spinner`) actually disappear.
- [x] **`CLAUDE.md`** — softened the "taxonomies are locked" line to
      "do not invent new entries autonomously; additions require
      explicit user approval." Phase count 10→11, page-type count
      17→21, component count ~45→~63.
- [x] **`taxonomy-additions.md` (new)** — working-session snapshot
      of the additions, with definitions. Points back to
      `docs/PROJECT.md` §2.1–§2.3 as the canonical source.

### Files changed
- `docs/PROJECT.md` — §2.1 (+1 row), §2.2 (+4 rows, 1 def edit),
  §2.3 (+17 rows, 1 def edit)
- `init_db.py` — `PHASES` / `PAGE_TYPES` / `COMPONENTS` lists +
  upsert/synonym-clear refactor of `seed_taxonomies()`
- `CLAUDE.md` — domain-model essentials reflect new counts
- `nextstep.md` — Session 8 block (this entry)
- `taxonomy-additions.md` (new) — session snapshot

### How to test — local (passed 2026-05-16)
1. `python init_db.py` — runs clean; second run is idempotent.
2. Row counts (`python -c "import sqlite3; …"`): `phases` 11,
   `page_types` 21, `components` 63.
3. Display order in DB matches `PROJECT.md` §2.x ordering exactly
   (verified by `SELECT display_order, slug FROM components ORDER BY
   display_order`).
4. `python app.py`. New routes resolve to 200 + Session 6 empty
   state: `/page-type/{pricing-page,confirmation-page,auth-page,
   404-page}` and `/component/{list,textarea,combobox,file-upload,
   stepper,code-block,chart,cookie-banner,spinner,loader,stat,rating,
   micro-feedback,audio,map,shopping-cart,copy-link-button}`.
5. Phase filter rail on `/page-type/article-page` shows all 11
   checkboxes including the new `Legal`. `/page-type/article-page`
   Content-Length 108855 (was 108614 in Session 7; +241 from the
   `Legal` checkbox in both rail and mobile dialog).
6. `/page-type/nonexistent` still 404. `/search?q=image` still 200.
7. Search synonym hygiene: searching `loader` no longer expands to
   `spinner` (verified by `SELECT synonym FROM synonyms WHERE
   entity_slug='spinner'` — no "Loader" row).

### How tested — production (passed 2026-05-16)
- Deployed via GHA `25958578000`, push `b02b94f`, ~10s.
- One-time prod seed via
  `ssh root@77.42.40.207 'cd /opt/bestpractice && python3 init_db.py'`
  ran clean: schema applied, taxonomies seeded (idempotent skip on
  existing fixtures), FTS rows 65. The new upsert logic re-ran on
  every existing row, syncing labels / definitions / display_order
  on the prod DB to match the canonical lists.
- Smoke test via VPS-local curl bypassing Caddy:
  `ssh root@77.42.40.207 'curl -sI http://localhost:5681/component/loader'`
  → `HTTP/1.1 200 OK`, Content-Length 13446 (Session 6 empty
  state). New slug routes are live.

### Out of scope (parked — Session 9)
- Slice C (ingestion + Groq scoring) — still queued, see Session 9
  pointer below.
- Fixture content for any new slug — all 21 new routes render the
  empty state until fixtures or Slice C ingestion lands.
- Re-tagging existing article-page sub-considerations with the new
  `legal` phase — editorial work, deferred.

### Lessons / decisions worth noting (non-obvious)
- **`INSERT OR IGNORE` + canonical-list ordering is a foot-gun.**
  Inserting a new row in the middle of `COMPONENTS` left every
  later existing row with its old `display_order` while new rows
  got fresh sequential numbers, producing duplicates and a scrambled
  order. The upsert pattern (`INSERT OR IGNORE` → unconditional
  `UPDATE`) keeps slug-as-PK semantics while letting the source-of-
  truth list dictate ordering. Worth the extra cursor call.
- **Synonyms decay silently.** Dropping "Loader" from `spinner`'s
  synonyms list does nothing on its own because the seed never
  DELETEd. Clear-then-fill per `(entity_type, entity_slug)` makes
  the list authoritative the same way the upsert does for the row
  itself. Switched the synonym INSERT from `OR IGNORE` to plain
  `INSERT` since the prior DELETE guarantees no conflict.
- **"Locked" taxonomies aren't forever.** `CLAUDE.md` framed all
  three taxonomies as locked; in practice the user wanted controlled
  additions when real gaps surfaced (cookie consent had no phase
  fit; lists/tables/notifications had design-stage ambiguity). New
  wording: "do not invent new entries autonomously; additions
  require explicit user approval." That preserves the guardrail
  against drift while admitting reality.
- **Distinguishing near-synonyms matters.** `spinner` vs `loader`,
  `rating` vs `micro-feedback`, `progress-bar` vs `spinner` vs
  `skeleton` — the temptation is to collapse, but each has
  meaningfully different considerations (size, semantics, what it
  signals). Definitions need to call out the distinction or the
  taxonomy degrades into vague overlap. Pattern: when adding a new
  slug near an existing one, sharpen the older definition in the
  same edit.

---

## Next session — Session 9 starts here

**Slice C — ingestion + Groq scoring.** First user-facing payoff is
real pending rows in `/admin/queue`. Reference the §6 ingestion
pattern in `PROJECT.md`; the working pattern lives in
AmuseAlot/musemaniac's `collect_news.py` (ETag caching, content-hash
dedup, langdetect) + `score_news.py` (retry/rate-limit, prompt
shape). Local path per Session 1's reference memory:
`E:\_dev\musemaniac`.

The navigation design that triggered Session 8's taxonomy audit is
still in progress at the user end — when it lands, building the
nav (selector to jump between page-types/components from any view)
is the natural pair-up before Slice C content fills in.

Order of operations for Slice C:
1. **`collect.py`** — iterate active `sources` rows, fetch feeds with
   ETag/Last-Modified caching, hash-dedup against
   `sub_considerations.body`, write candidates into
   `sub_considerations` with `status='pending'`,
   `relevance_score=NULL`.
2. **`score.py`** — Groq-score pending rows 1–10 against the page
   type / component routing guidance from `PROJECT.md`, write back
   to `relevance_score`. Items below a threshold (e.g. 4) stay
   pending but won't bubble to the top of the queue.
3. **`/admin/queue` write paths** — approve / reject / edit-and-
   approve POST handlers. The `<dialog>` from `BUILD_NOTES.md` §2.3
   is the prototype contract for edit-and-approve. The
   `setupMobileDialog` pattern from Session 7 is reusable; the
   edit modal probably wants its own dedicated dialog rather than
   sharing.

### Tech-debt nudges parked from earlier sessions
- VPS Python is 3.10.12; `PROJECT.md` §8 calls for 3.12+. No 3.12-
  only syntax used yet; flag if Slice C reaches for it.
- Daily SQLite backup cron + log rotation on the VPS — last unchecked
  item from Session 2's deploy-prep list. Ingestion makes this more
  urgent (DB is no longer purely append-on-deploy).
- Radix Themes CSS vendoring — `tokens.css` already uses Radix-shaped
  variable names; mechanical swap, can land any time.
- `filters.js` is 101 lines; trim to under 100 next time it's
  edited.
- Add a fixture-content validator in `init_db.py` for unescaped
  structural HTML tags (see "Out of scope" above).
- `actions/checkout@v4.2.2` is Node-20-deprecated; bump before
  2026-06-02.
