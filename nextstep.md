# bestpractice — next steps

Last updated: 2026-05-16 (Session 5 — admin queue + sources)

This file is the running session log. Format follows the convention used in
`E:\_dev\bubble` (`docs/nextstep.md`): numbered sessions with narrative +
Done checkboxes + Files changed + How to test + Next-session pointer. When
this file passes ~400 lines and has 4+ completed sessions, archive the
oldest sessions to `docs/archive/sessions.md` and keep the 3 most recent
live here.

Sessions 1–2 (project bootstrap, design prototype + deploy prep) live in
[`docs/archive/sessions.md`](docs/archive/sessions.md).

---

## Session 3 — Build Slice A (read surface) ✅ shipped 2026-05-16

Slice A of the build session per `C:\Users\calle\.claude\plans\whats-next-breezy-pebble.md`:
smallest deployable read surface. Flask app, full schema, taxonomies seeded
from `PROJECT.md` §2.1–2.3, prototype's 18 considerations / 59 sub-accordions
imported as fixtures, `/page-type/article-page` renders identically to
`prototype/page-type.html`. No search, no admin, no ingestion. Slices B+
(search, admin shells, ingestion, scoring) are follow-up sessions.

Local build complete and verified. First production deploy fired
cleanly via the Session 2 GHA workflow: rsync + `systemctl restart
bestpractice` → `active` in ~12s. After seeding the VPS DB
(`python3 init_db.py` on the box, one-time), `curl localhost:5681
/page-type/article-page` from the VPS returns 200 with 107,695 bytes
— byte-identical content-length to local. Sibling-site check held:
amusealot.com 200, bubblesdontcry.com 200, staging.bubblesdontcry.com
401, all unchanged.

### Done — local
- [x] `schema.sql` — all eight tables from `PROJECT.md` §4 (`phases`, `page_types`, `components`, `synonyms`, `considerations`, `sub_considerations`, `sub_consideration_phases`, `sources`). `PRAGMA foreign_keys = ON`. Indices on `parent_slug` (considerations) and `consideration_id` (sub_considerations). Added a `position` column on `sub_consideration_phases` so the rendered chip order matches the fixture (without it, SQLite's PK index made phases alphabetical, breaking parity with the prototype's `data-phases="strategy concept content"` order).
- [x] `init_db.py` — applies schema, seeds 10 phases / 17 page_types / 46 components (all from `PROJECT.md` §2.1–2.3) and their synonyms (114 rows), loads `fixtures/article_page.json` into `considerations` + `sub_considerations` + `sub_consideration_phases`. Idempotent (`INSERT OR IGNORE` on taxonomies; skip fixture import if `article-page` already has considerations). Site-wide group inside the fixture is bucketed under `parent_slug='site-wide'`, not duplicated into every page type — matches `PROJECT.md` §2.2 ("not a real page" — cross-cutting).
- [x] `scripts/extract_article_page_fixture.py` — one-shot bs4 parser that turns `prototype/page-type.html` into `fixtures/article_page.json`. Extracts 6 groups (5 page-type + 1 site-wide), 18 considerations, 59 sub-accordions including phases, source name/suffix/title/URL/date, body HTML, and `display_order`. The `sub--new` class is **not** stored; `last_updated` is stamped per `BUILD_NOTES.md` §3 (compute at render time from a 14-day window). For the four `sub--new` subs in the prototype, the extractor stamps `last_updated` near the `NEW_ANCHOR` (2026-05-15) spread by 3-day intervals so the indicators stay live for ~a week post-deploy then decay naturally.
- [x] `fixtures/article_page.json` (61 KB) — extractor output committed so `init_db.py` has no bs4 runtime dep.
- [x] `static/styles/{tokens,base,components}.css`, `static/js/{accordion,filters,search}.js` — copied verbatim from `prototype/`. CSS file names preserved per `BUILD_NOTES.md` §1.
- [x] `static/fonts/InterVariable.woff2` (344 KB) — Inter v4 variable font from `rsms.me/inter/font-files/`. `@font-face` declaration added at the top of `static/styles/base.css`; Google Fonts CDN `<link>` and preconnects dropped from `templates/base.html`. `tokens.css`'s `--font-sans: "Inter", ...` picks it up without further changes.
- [x] `templates/base.html` — shared chrome with brand, search form (action → `/search`), admin nav. Three CSS files and three JS files loaded via `url_for('static', filename=…)`.
- [x] `templates/page_type.html` — extends `base.html`. Two macros (`render_consideration`, `render_sub`) emit the prototype's DOM contract from `BUILD_NOTES.md` §3 verbatim: `id="{cons_slug}.{sub_slug}"`, space-separated `data-phases`, `data-role="count"`, `sub--new` class computed at render time via an `is_new` Jinja filter, `<span class="sub__newdot">` + `<span class="sr-only">New. </span>` pair, the chevron SVG. Filter rail iterates `phases` from the DB; site-wide group renders last with `hidden` (the `filters.js` toggle un-hides it client-side per `BUILD_NOTES.md` §2.1).
- [x] `templates/placeholder.html` — friendly "coming in a later slice" page used by `/search`, `/admin/queue`, `/admin/sources` so the header chrome's links route somewhere reasonable until Slice B+. Skips loading the JS files (filters/accordion/search), since there's nothing to filter on a placeholder.
- [x] `app.py` — single-file Flask, ~170 lines. Routes: `/` (302 → article-page), `/page-type/<slug>` (loads page_type + phases + considerations + sub-considerations + phase tags, builds the grouped view model, also appends a site-wide group from `parent_slug='site-wide'` when the requested page isn't site-wide), `/search`, `/admin/queue`, `/admin/sources` (placeholders). `is_new` Jinja filter computes "within 14 days of now (UTC)" per `BUILD_NOTES.md` §3. `DB_PATH` reads `BESTPRACTICE_DB` env var with `data/bestpractice.db` default, so systemd's `EnvironmentFile=/opt/bestpractice/.env` can override on the VPS without code changes. Exits with a clear "run `python init_db.py` first" message if the DB file is missing — avoids surprise writes from a misconfigured service start. Listens on `0.0.0.0:5681` to match the `bestpractice.service` unit installed in Session 2.

### Files changed
- `app.py` (new, ~170 lines)
- `schema.sql` (new)
- `init_db.py` (new)
- `scripts/extract_article_page_fixture.py` (new)
- `fixtures/article_page.json` (new)
- `templates/base.html` (new)
- `templates/page_type.html` (new)
- `templates/placeholder.html` (new)
- `static/styles/{tokens,base,components}.css` (copied from `prototype/styles/`)
- `static/js/{accordion,filters,search}.js` (copied from `prototype/js/`)
- `static/fonts/InterVariable.woff2` (new binary, 344 KB)
- `nextstep.md` — Session 3 block (this entry)

### How to test — local (passing as of 2026-05-15)
1. `python init_db.py` → creates `data/bestpractice.db`. Re-running prints `(skip) article-page already has 18 considerations` and exits clean.
2. `python app.py` → serves on `http://localhost:5681`.
3. `curl -sI http://localhost:5681/` → 302 to `/page-type/article-page`.
4. `curl -sI http://localhost:5681/page-type/article-page` → 200, ~108 KB HTML.
5. DOM contract parity (counted from the served HTML with bs4): 6 groups, 18 considerations, 59 sub-accordions, 4 `sub--new`, 10 phase checkboxes, `#toggle-sitewide` present, the site-wide `<section>` carries `hidden`. The first sub's `id` is `page-purpose.one-job`, `data-phases` is `strategy concept content`, chips render in matching order.
6. `curl -sI http://localhost:5681/page-type/nonexistent` → 404.
7. `/search`, `/admin/queue`, `/admin/sources` → 200 with the placeholder template.
8. `curl -sI http://localhost:5681/static/{styles/base.css,fonts/InterVariable.woff2,js/accordion.js}` → all 200.
9. Open `http://localhost:5681/page-type/article-page` in a browser side-by-side with `file:///E:/_dev/best/prototype/page-type.html`. Spot-check: untick a phase checkbox (subs hide, empty cons collapse, empty group disappears), toggle "Show site-wide considerations" (site-wide group appears at the bottom), append `#page-purpose.one-job` to the URL and reload (both `<details>` open).

### How tested — production (passed 2026-05-16)
- GHA run `25943254092` completed in 12s, rsync + `systemctl is-active bestpractice` returned `active`.
- The service starts cleanly with no DB (the app only checks for the DB at request time, not on startup). So the deploy chain reports green even pre-seed, and the actual first 500 would only show on a request — fine, it's a known state.
- `ssh root@77.42.40.207 'cd /opt/bestpractice && python3 init_db.py'` ran once. Seeded 18 considerations and 59 sub-considerations.
- `ssh root@77.42.40.207 'curl -sI http://localhost:5681/page-type/article-page'` → 200, Content-Length 107695 — byte-identical to the local Werkzeug response. Werkzeug header reports `Python/3.10.12` on the VPS (see Lessons).
- Sibling check: `https://amusealot.com` 200, `https://bubblesdontcry.com` 200, `https://staging.bubblesdontcry.com` 401, `https://best.amusealot.com` 401. The new site's 401 confirms Caddy is reaching the app behind basic auth.

### Out of scope (parked — Slice B+)
- `/search` route — server-side body/title text search, synonyms-driven query expansion, the "Includes synonym matches for *foo*" hint line, snippet generation with `<mark>` highlights.
- Admin shells: `/admin/queue` (no items yet without ingestion), `/admin/sources` (lists `sources` table rows), `/admin/considerations/<slug>` (large-accordion editor).
- `/component/<slug>` route. Schema supports `parent_type='component'` but no template/route wiring yet. The `page_type.html` template will be reused per `BUILD_NOTES.md` §2.1.
- Other page types beyond Article Page. Currently they 404 cleanly; render an empty state in Slice B.
- RSS ingestion pipeline (`collect.py` mirroring musemaniac's `collect_news.py`): ETag caching, content-hash dedup, langdetect, retry behavior.
- Structured importers (caniuse, WCAG 2.2 JSON-LD, MDN BCD, Schema.org).
- Groq scoring (`score.py` mirroring `score_news.py`) — never auto-publishes per `PROJECT.md` §6.2.
- Daily SQLite backup cron + log rotation on the VPS (last unchecked item in Session 2's deploy-prep list).
- Radix Themes CSS vendoring — `tokens.css` already uses Radix-shaped variable names per the prototype's `DECISIONS.md`, so this is a mechanical swap that can land any time.

### Lessons
- **VPS Python is 3.10.12, not 3.12+.** `PROJECT.md` §8 spec'd "Python 3.12+". Slice A's code uses no 3.12-only syntax so it runs clean, but the constraint should be reconciled — either upgrade `/usr/bin/python3` on the VPS (or use a `pyenv`/`uv` install pinned to 3.12) before any feature that needs newer typing/syntax lands. Flag in Slice B if relevant.
- **First-deploy hand-step is acceptable.** Seeding the DB by SSH'ing in once isn't wrapped into the GHA workflow — adding `python3 init_db.py` to the deploy script would make subsequent deploys re-run the seed (idempotent, but wasteful, and a foot-gun if the seed ever stops being idempotent). Keep it manual until ingestion exists.

### Decisions worth noting (non-obvious)
- **Site-wide is its own bucket, not denormalised per page type.** The fixture's site-wide group is stored under `parent_slug='site-wide'`. The view function pulls main considerations from the requested slug AND site-wide considerations separately, then concatenates them as a trailing `hidden` group. This avoids duplicating cross-cutting items into every page-type row when more page types ship in Slice B.
- **`source_title` is its own column.** The prototype's per-sub footer carries a work/article title (`<em>How users read on the web</em>`) that isn't visible in the metarow. Adding `source_title` to `sub_considerations` lets the footer reconstruct faithfully without storing the prototype's footer HTML verbatim.
- **`init_db.py` is hand-run, not auto-run on app start.** Avoids surprise writes from a misconfigured service start. The app exits cleanly if the DB is missing.
- **Werkzeug dev server in production.** Matches musemaniac's pattern (`ExecStart=/usr/bin/python3 .../app.py`). Single user behind Caddy basic auth; gunicorn would be over-engineered for the load shape.

---

## Session 4 — Slice B part 1: /search ✅ shipped 2026-05-16

First slice of the search + admin trio. Wired `/search` end-to-end:
SQLite FTS5 over `sub_considerations` (with parent `consideration.title`
and `consideration.intro` folded in), whole-query synonym expansion
against the seeded `synonyms` table, grouped results that mirror
`prototype/search.html`, `<mark>`-highlighted snippets via FTS5's
built-in `snippet()`. Admin shells (`/admin/queue`, `/admin/sources`)
are still placeholders — Session 5.

### Done
- [x] `schema.sql` — `subs_fts` virtual table (FTS5, `unicode61
      remove_diacritics 2`, content columns `one_liner` / `body` /
      `cons_title` / `cons_intro`). Contentless: no triggers,
      `init_db.py` owns sync.
- [x] `init_db.py` — new `rebuild_fts()` runs on every invocation. Joins
      approved subs to their approved consideration parent, repopulates
      the FTS table from scratch. Cheap, idempotent, picks up content
      drift without migrations.
- [x] `app.py` — `expand_synonyms()` does case-insensitive whole-query
      lookups against `synonyms.synonym` and entity labels
      (page_types/components/phases); for each hit, returns the
      entity's other names. `run_search()` builds an FTS query of the
      form `"<q>" OR "<expansion>" …`, fetches results with FTS5's
      `snippet()` for `<mark>` highlights on both `body` and
      `one_liner` columns, then groups by parent (page types in
      `display_order`, then components, then site-wide). The route
      catches `sqlite3.OperationalError` (raised when FTS rejects
      special chars like a bare `"`) and renders the empty state
      instead of 500ing.
- [x] `templates/search.html` — extends `base.html`, ports the
      prototype's DOM verbatim. Three states: no query (prompt),
      no matches (empty state with synonym-suggestion list), hits
      (`<p class="results-meta">` line + grouped `<section
      class="result-group">` blocks). Result links resolve to
      `/page-type/<slug>#<cons>.<sub>` so the existing hash-deep-link
      JS opens the right accordions on landing.

### Files changed
- `schema.sql` — `subs_fts` virtual table appended
- `init_db.py` — `rebuild_fts()` + main() call
- `app.py` — `_fts_quote`, `expand_synonyms`, `run_search`, replaced
  `/search` route body
- `templates/search.html` (new)

### How to test — local (passed 2026-05-16)
1. `python init_db.py` → final line `FTS rows: 59`.
2. `python app.py`.
3. `curl -sI http://localhost:5681/search?q=alt+text` → 200, ~3.8 KB.
4. `curl -s 'http://localhost:5681/search?q=image'` → 7 results, meta
   line includes `Includes synonym matches for <em>Picture</em>.`
5. `curl -s 'http://localhost:5681/search?q=nav'` → 3 results, meta
   line expands to `main nav`, `menu`, `Navigation` (the `navigation`
   component's other names).
6. `curl -s 'http://localhost:5681/search?q=zzzzzzz'` → empty-state
   "No matches for &ldquo;zzzzzzz&rdquo;." rendered.
7. `curl -s 'http://localhost:5681/search?q=%22'` (bare `"`) → 200
   empty state, **not 500** (verifies the OperationalError fallback).
8. `curl -sI http://localhost:5681/page-type/article-page` → still
   200, Content-Length 107695 (unchanged from Slice A).

### How tested — production (passed 2026-05-16)
- Push to `main` triggered GHA; service came back `active`.
- One-time `ssh root@77.42.40.207 'cd /opt/bestpractice && python3
  init_db.py'` to add `subs_fts` to the existing prod DB. Output:
  `FTS rows: 59` — matches local.
- `curl -sI http://localhost:5681/search?q=alt+text` from the VPS →
  `HTTP/1.1 200`.
- `curl -s 'http://localhost:5681/search?q=image' | grep -o
  'class=.result.' | wc -l` → 33 (= 7 results × 4 `result__*` classes
  + 1 group × ~4 `result-group__*` classes + chip). Matches local
  shape.

### Out of scope (parked — Session 5 starts here)
- `/admin/queue` — read-only shell first; the queue is empty until
  ingestion lands in Slice C, so the page renders "no pending items"
  with the toolbar (Last sync pill + status counts wired to real data
  once `sources` rows exist).
- `/admin/sources` — list + active/paused toggle over the `sources`
  table; `<form method="post">` per row, no JS required for the
  toggle.
- `/component/<slug>` — reuses `templates/page_type.html`; just a
  different `parent_type` filter on the considerations query plus a
  template fall-through to the existing `page_type` view.
- Empty-state rendering for the 16 other page types so they stop 404ing.

### Lessons / decisions worth noting (non-obvious)
- **FTS5 with `content=''` (contentless) was tempting but rejected.**
  Contentless FTS forbids `snippet()` / `highlight()` because the
  source text isn't stored, only the index. We need snippets for the
  result UI, so the table stores its own copy. Cost: ~one extra copy
  of every sub's body in the DB. Worth it.
- **Synonym expansion is whole-query, not tokenized.** Matching the
  whole user query against `synonyms.synonym` (case-insensitive) keeps
  the surface predictable: typing `nav` expands, typing `nav menu`
  doesn't. Multi-token expansion can land later if real usage
  demands it.
- **Snippet column priority.** Result rendering prefers the `body`
  snippet (longer, more context) when FTS injected a `<mark>` there;
  falls back to the `one_liner` snippet otherwise. If the match lived
  in `cons_title` / `cons_intro` instead of the sub itself, neither
  snippet carries a mark — the result still groups correctly and
  shows the raw one-liner, just unhighlighted. Acceptable for v1; a
  future polish is emitting an "in: *<Cons title>*" hint when the
  match column is cons-level.
- **`init_db.py` always rebuilds FTS.** The fixture-load step is still
  skip-if-present, but FTS rebuild is unconditional. That means
  rerunning `init_db.py` after any future content edit re-syncs the
  index automatically. The admin write paths in Slice C/D will need
  to update FTS row-by-row instead of relying on this rebuild.

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

## Next session — Session 6 starts here

Two unfinished items from Session 5's punch list, then Slice C kicks
off ingestion:

1. **`/component/<slug>`** — reuse `templates/page_type.html`. Rename
   `load_page_type_view` to `load_parent_view(parent_type,
   parent_slug)`; mount route at `/component/<slug>`; pass
   `parent_type='component'`. Seed `image` or `card` considerations
   so the route renders non-empty for at least one component.
2. **Empty-state for the other 16 page types.** Currently they 404.
   Render `page_type.html` with `groups=[]` and a friendly "no
   considerations yet" body inside the page_type macro so the chrome
   still shows. The route already loads `page_type` row before
   considerations, so this is mostly a template branch.

Then **Slice C** (ingestion + Groq scoring): see the §6 ingestion
pattern in `PROJECT.md` and AmuseAlot/musemaniac's `collect_news.py`
+ `score_news.py` for the working pattern. First pending rows in the
queue come from this slice — that's the trigger to wire approve /
reject / edit POST handlers in `/admin/queue`.

### Tech-debt nudges parked from earlier sessions
- VPS Python is 3.10.12; `PROJECT.md` §8 calls for 3.12+. No 3.12-only
  syntax has been used; flag if a Slice C/D feature reaches for it.
- Daily SQLite backup cron + log rotation on the VPS — last unchecked
  item from Session 2's deploy-prep list.
- Radix Themes CSS vendoring — `tokens.css` already uses Radix-shaped
  variable names; mechanical swap, can land any time.
