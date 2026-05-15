# bestpractice — next steps

Last updated: 2026-05-15 (Session 2 — Design in progress + deploy prep)

This file is the running session log. Format follows the convention used in
`E:\_dev\bubble` (`docs/nextstep.md`): numbered sessions with narrative +
Done checkboxes + Files changed + How to test + Next-session pointer. When
this file passes ~400 lines and has 4+ completed sessions, archive the
oldest sessions to `docs/archive/sessions.md` and keep the 3 most recent
live here.

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

## Next session — Session 4 starts here

The discrete next step is **the first production deploy** — push Session 3
to `main`, watch GHA, run `init_db.py` once on the VPS, enable the
service, verify, sibling-site check. After that lands cleanly, Slice B
(search + admin shells) is the natural next slice.

When Slice B starts, the order is roughly:
1. `/search` route — server-side text search across consideration titles, sub one-liners, and sub bodies. Use SQLite FTS5 (a virtual table populated from `sub_considerations`) for the body matches; bolt on a small synonym-aware client-side expander in `static/js/search.js`. Group results by `parent_type/parent_slug` per `BUILD_NOTES.md` §2.2.
2. `/admin/queue` — read-only at first (empty queue until ingestion exists), then editable forms when the data starts flowing.
3. `/admin/sources` — list-and-toggle UI over the `sources` table.
4. Then ingestion + Groq scoring (Slice C).

Before the first deploy: confirm port 5681 is still unclaimed on `77.42.40.207`,
confirm Caddy's existing site blocks for `bubble`, `bubblesdontcry-site`,
and `amusealot` are untouched, and verify the basic-auth password for
`best.amusealot.com` is recorded somewhere the user can recover it.
