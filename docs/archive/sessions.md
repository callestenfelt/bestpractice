# bestpractice — archived sessions

Older entries from `nextstep.md`, archived once the live log passed the
~400-line threshold. Sessions stay in chronological order. Add new
archived blocks at the bottom (push the live log's oldest down).

---

## Session 1 — Project bootstrap ✅ shipped 2026-05-15

Took the repo from a docs-only state to a real git repo connected to
`https://github.com/callestenfelt/bestpractice.git`. No application code
yet — that waits for the design prototype per `docs/DESIGN_HANDOVER.md`
and a later build session per `docs/PROJECT.md` §12.

### Done
- [x] `docs/PROJECT.md` — project brief (authored prior to this session)
- [x] `docs/DESIGN_HANDOVER.md` — design agent brief (authored prior)
- [x] `CLAUDE.md` — orientation for future Claude Code instances (authored prior)
- [x] `.gitignore` — Python + Flask + SQLite + OS/editor patterns
- [x] `nextstep.md` — this file, session log
- [x] `git init -b main` and explicit initial commit
- [x] `origin` remote pointed at `https://github.com/callestenfelt/bestpractice.git`
- [x] Pushed `main` to GitHub

### Files changed
- `.gitignore` (new)
- `nextstep.md` (new)

### How to test
1. `git remote -v` shows exactly `origin → https://github.com/callestenfelt/bestpractice.git` (fetch + push) and no other remotes.
2. `git status` is clean on `main`.
3. `git log --oneline` shows one commit on `main`.
4. Open `https://github.com/callestenfelt/bestpractice` in a browser — `CLAUDE.md`, `.gitignore`, `nextstep.md`, and the two files under `docs/` are visible.

### Out of scope (parked — for future sessions)
- Flask app skeleton (`app.py`, Jinja templates, `static/`).
- SQLite `schema.sql` with seeded taxonomies (phases, page types, components).
- RSS ingestion pipeline (pattern: AmuseAlot's `collect_news.py`).
- Structured-data ingestion (caniuse, WCAG 2.2 JSON-LD, MDN BCD, Schema.org).
- Groq + Llama 3.3 scoring pass + admin review queue (pattern: AmuseAlot's `score_news.py`).
- `Caddyfile` snippet for `best.amusealot.com`.
- `bestpractice.service` systemd unit (port 5681 per `docs/PROJECT.md` §7 — must confirm unclaimed on the VPS first).
- `.github/workflows/deploy.yml` — adapt the bubble / bubblesdontcry-site pattern for `main` (their workflows trigger on `master`).
- `.env` template and the `set -a; source .env; set +a` loader script.
- `prototype/` folder — owned by Claude Design, not Claude Code.

### Safety note
This session did **not** SSH to `77.42.40.207`, did **not** touch Caddy
on the VPS, and did **not** bind any new ports. The three sibling sites
(`bubble`, `bubblesdontcry-site`, `amusealot`) are unaffected. Keep this
property until the build agent is ready to deploy — and at that point,
verify the three siblings are still serving cleanly **before and after**
each deploy.

---

## Session 2 — Design prototype ✅ shipped 2026-05-15

Claude Design is producing the `prototype/` folder per
`docs/DESIGN_HANDOVER.md`: four static HTML views (`page-type.html`,
`search.html`, `admin-queue.html`, `admin-sources.html`), Radix Themes
CSS vendored, Inter self-hosted, vanilla JS only, no build step. This
Claude Code session is **not** doing design work — we only handle code,
infra, and the running session log.

### Working in parallel
- Design work happens in its own branch/folder. When the prototype lands,
  it should be **added under `prototype/`** so it sits alongside (not
  inside) `docs/`.
- The repo is untouched on this end while design is in flight; no merge
  conflicts to manage.
- Push frequency on Claude Design's side is their call — this log will
  reflect their commits when they arrive.

### Prototype review — done 2026-05-15
v1 of the prototype passed every structural item in the checklist below
but expanded the blue accent beyond the strict `CLAUDE.md` rule ("new"
indicator + active/focus only) to also cover links, primary CTAs,
`<mark>` highlights, and a `.chip--blue` utility class. Sent back to
Claude Design with two asks: (1) write down the full approved list of
blue uses so the build agent has a deterministic rule, (2) remove
anything in that list that isn't actually used. Claude Design returned
prototype2 with exactly that — a new "Blue accent — definitive list" §
in `DECISIONS.md` enumerating 7 approved uses, `.chip--blue` removed
from `components.css`, and a `BUILD_NOTES.md` callout explaining the
intentionally-missing `assets/` folder (inline SVG icons + Google Fonts
CDN are both deliberate; build agent does the self-hosting swap).
prototype2 promoted to canonical `prototype/`, v1 discarded (was never
committed). Five HTML files, three CSS files, three JS files (all
<100 lines), 18 considerations across 5 content groups + a site-wide
group with `hidden`, 59 sub-accordions, 10 phases in the filter rail.

### Review checklist (results)
The checklist was derived from `docs/DESIGN_HANDOVER.md` constraints
and applied to the prototype before approval.

- [x] `prototype/` exists with the five HTML files, `styles/`, `js/` (`assets/` deliberately omitted — see DECISIONS / BUILD_NOTES).
- [x] Each HTML file opens directly from the filesystem — no server required, no build step.
- [x] Vanilla JS only; each JS file under ~100 lines (59 / 69 / 29); no React/Vue/Svelte/bundler.
- [x] Native `<details>`/`<summary>` for accordions; `<input type="search">` for search. No `<dialog>` yet — "Edit & approve" modal deferred to build, flagged in `DECISIONS.md`.
- [x] Light mode only. No `prefers-color-scheme` or dark-mode CSS.
- [x] Blue accent uses documented as a definitive 7-item list in `prototype/DECISIONS.md` ("Blue accent — definitive list" §). Build agent: don't add an eighth without asking.
- [x] "New" indicator is not color-alone — paired with sr-only "New. " text (per accessibility note in `DESIGN_HANDOVER.md`).
- [x] `page-type.html` populated with Article Page content: 18 large accordions across 5 groups (Before you start / Top of page / Body / End of page / Behind the scenes) plus the site-wide group rendered `hidden`. 59 sub-accordions total (≈3.3 per consideration, within the 3–8 target). Sources realistic (NN/g, web.dev, WCAG, MDN, caniuse, A11y Project).
- [x] Filter rail has all ten phases from `PROJECT.md` §2.1, all checked by default, plus the "Show site-wide considerations" toggle (`#toggle-sitewide`) off by default.
- [x] Hash-state deep links work: `accordion.js` parses comma-separated `top-id` or `top-id.sub-id` entries and forces `open` on the matching `<details>` elements.
- [x] Filter-driven hiding works: `filters.js` hides subs whose `data-phases` don't intersect active set, then collapses out empty considerations, then empty group sections.
- [x] `search.html` echoes the query (`[data-role="query-echo"]` + input `value`) and shows results grouped by parent.
- [x] `admin-queue.html` and `admin-sources.html` are functional rather than pretty (per the brief).
- [⏭] Inter variable font is self-hosted — deferred to build session (prototype loads from Google Fonts CDN for portability; see `BUILD_NOTES.md` §1).
- [⏭] Radix Themes CSS is vendored — deferred to build session (prototype uses its own gray/blue scales with Radix-shaped variable names; see `DECISIONS.md` Tokens §).
- [x] `prototype/DECISIONS.md` exists with one bullet per noteworthy decision.

### Files changed
- `prototype/` (new, 13 files) — five HTML views, three CSS files, three JS files, `BUILD_NOTES.md`, `DECISIONS.md`. Top-level (not under `docs/`) so the path matches `BUILD_NOTES.md` §1's file-mapping table.
- `nextstep.md` — Session 2 block updated with checklist results + this Files-changed entry.
- `.github/workflows/deploy.yml` — added earlier in the session (see Deploy prep below).

### How to test
1. Open `prototype/index.html` directly from the filesystem — should redirect to `page-type.html`.
2. On `page-type.html`: scroll the five groups, expand a large accordion, expand a sub. Untick a phase checkbox and watch subs hide. Tick the "site-wide" toggle and watch a new group appear at the bottom.
3. Append `#some-cons-id.some-sub-id` to the URL and reload — both accordions should open on load.
4. Click the search button in the header → lands on `search.html?q=…` with results grouped by parent and the query echoed in the input.
5. Visit `admin-queue.html` and `admin-sources.html` — verify they render without errors.

### Deploy prep — done in parallel with design work
Done while waiting on the design prototype so the build session has fewer
blockers. No secret values appear in this repo; only names and structure.

- [x] GitHub Actions secrets added to `callestenfelt/bestpractice` (Settings → Secrets and variables → Actions):
  - `SSH_PRIVATE_KEY` — same ED25519 key musemaniac's `deploy.sh` uses
  - `SSH_HOST` — VPS IP (already public in `docs/PROJECT.md` §7)
  - `SSH_USER` — `root`
  - `SSH_KNOWN_HOSTS` — three host key lines pulled from the local `~/.ssh/known_hosts` (Windows' shipped `ssh-keyscan` couldn't negotiate the VPS's post-quantum KEX `sntrup761x25519-sha512@openssh.com`; pulling from existing trusted entries is the cleaner path anyway)
- [x] SSH auth verified end-to-end: `ssh -i ~/.ssh/id_ed25519 root@77.42.40.207 "echo ok; hostname"` returns `ok` and the VPS hostname.
- [x] DNS: `A` record `best.amusealot.com → 77.42.40.207` added at Namecheap (Advanced DNS tab, Host = `best`). Verify with `nslookup best.amusealot.com` once propagated. No Cloudflare in front, so Caddy will get a Let's Encrypt cert directly via HTTP-01 on first request.

### Deploy prep — still pending (build agent will handle)
- [x] `/opt/bestpractice/.env` on the VPS, 2026-05-15. Reused musemaniac's `GROQ_API_KEY` by piping the line directly: `grep ^GROQ_API_KEY= /opt/musemaniac/.env > /opt/bestpractice/.env` (avoids copy-paste contamination — the first attempt via PowerShell ended up with `GROQ_API_KEY=GROQ_API_KEY=gsk_...` because the whole line had been pasted as the value). File is `root:root 600`, 70 bytes (13 + 56-char key + newline).
- [x] Confirm port `5681` is free on the VPS: `ss -tlnp | grep 5681` returned nothing on 2026-05-15; sanity-check `grep 5680` confirmed musemaniac listening on 5680 (`python3` pid 233037). 5681 cleared for bestpractice.
- [x] Caddy site block for `best.amusealot.com` added 2026-05-15. Pattern follows `staging.bubblesdontcry.com`: HSTS + `header -Server` + `X-Robots-Tag noindex,nofollow` + `encode zstd gzip` + `basic_auth { calle <bcrypt-hash> }` + `reverse_proxy localhost:5681`. Block appended at end of `/etc/caddy/Caddyfile` (not inserted near the other `*.amusealot.com` blocks — tidiness can wait, append-only is the lowest-risk edit). Backup saved as `Caddyfile.bak.1778877083`. Username `calle`. `caddy validate` passed; `systemctl reload caddy` clean; Let's Encrypt cert obtained via `tls-alpn-01` in ~5s. Verified end-to-end with `curl --resolve best.amusealot.com:443:77.42.40.207 -I https://best.amusealot.com` → `HTTP/1.1 401 Unauthorized` with `WWW-Authenticate: Basic`. Sibling sites confirmed untouched: amusealot.com 200, bubblesdontcry.com 200, staging.bubblesdontcry.com 401.
- [x] `bestpractice.service` systemd unit written at `/etc/systemd/system/bestpractice.service`, 2026-05-15. Mirrors `musemaniac-subscriber.service`: `Type=simple`, `User=root`, `WorkingDirectory=/opt/bestpractice`, `EnvironmentFile=/opt/bestpractice/.env`, `ExecStart=/usr/bin/python3 /opt/bestpractice/app.py`, `Restart=always`, `RestartSec=5`, `WantedBy=multi-user.target`. Port 5681 lives in `app.py`, not the unit. `systemctl daemon-reload` clean; status shows `Loaded: loaded; disabled; inactive (dead)`. Intentionally not enabled or started — no `app.py` yet, build session will deploy code then `systemctl enable --now bestpractice`. Running as root matches musemaniac's pattern; hardening (dedicated user, NoNewPrivileges, ProtectSystem, etc.) deferred to post-v1.
- [x] `.github/workflows/deploy.yml` added 2026-05-15. Triggers on push to `main` with `paths-ignore` for docs/`nextstep.md`/`CLAUDE.md`/`.gitignore`/`.claude/**` so doc-only commits don't spin a runner. Uses our four SSH secrets (`SSH_PRIVATE_KEY`, `SSH_HOST`, `SSH_USER`, `SSH_KNOWN_HOSTS`) — pre-stored known_hosts because Windows ssh-keyscan can't negotiate the VPS's KEX. Gated on `app.py` existing so the workflow runs green on doc/scaffold-only repos: when `app.py` lands, rsync + `systemctl restart bestpractice` start firing. Rsync excludes `.git/`, `.github/`, `.claude/`, `docs/`, `nextstep.md`, `CLAUDE.md`, `.gitignore`, `__pycache__/`, `*.pyc`, `.venv/`, `.pytest_cache/`, `*.db`, `*.sqlite*`, `instance/`. **Intentionally no `--delete` flag** — the SQLite DB lives next to the app; build agent should revisit this when finalizing data layout (likely move DB to `/opt/bestpractice-data/` so `--delete` becomes safe). `workflow_dispatch` enabled for manual runs.
- [ ] Daily SQLite backup cron and log rotation on the VPS.

### Lessons
- Windows' built-in OpenSSH `ssh-keyscan` (in `C:\Windows\System32\OpenSSH\`) is too old for the VPS's modern KEX list. When you need host keys on Windows, pull them from your existing `~/.ssh/known_hosts` instead of running keyscan. Anyone you've previously SSHed to is already a trusted entry.
- Musemaniac is the repo name for what `docs/PROJECT.md` calls "AmuseAlot". Local path: `E:\_dev\musemaniac`. When the briefs reference `collect_news.py`, `score_news.py`, or `run_newsletter.sh`, look there.
- Musemaniac deploys via local `deploy.sh` (scp + ssh systemctl restart), **not** GitHub Actions. Bestpractice will be the first Python-on-VPS project to use GHA-on-push — no existing workflow to copy.

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
