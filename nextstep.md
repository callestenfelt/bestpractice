# bestpractice — next steps

Last updated: 2026-05-15 (Session 2 — Design prototype in progress with Claude Design)

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

## Session 2 — Design prototype 🟡 in progress (started 2026-05-15)

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

### When Claude Design hands back — review checklist
Use this before approving so the build session has a clean input. The
checklist is derived from `docs/DESIGN_HANDOVER.md` constraints.

- [ ] `prototype/` exists with the five HTML files, `styles/`, `js/`, `assets/` layout described in the brief.
- [ ] Each HTML file opens directly from the filesystem — no server required, no build step.
- [ ] Vanilla JS only; each JS file under ~100 lines; no React/Vue/Svelte/bundler.
- [ ] Native `<details>`/`<summary>` used for accordions; `<input type="search">` for search; `<dialog>` if any modal exists.
- [ ] Light mode only. No dark-mode CSS variables or toggle.
- [ ] Blue accent appears **only** on the "new" indicator and active filter / focus states. Nothing else.
- [ ] "New" indicator is not color-alone — paired with a shape or text cue (per accessibility note in `DESIGN_HANDOVER.md`).
- [ ] `page-type.html` is populated with Article Page content: 12–18 large accordions across the four groups (Before you start / Top of page / Body / End of page / Behind the scenes), 3–8 sub-accordions each, fake-but-plausible sources (NN/g, web.dev, W3C/WCAG, A11y Project, MDN, caniuse), realistic dates and phase tags.
- [ ] Filter rail has all ten phases from `PROJECT.md` §2.1, all checked by default, plus the "Show site-wide considerations" toggle off by default.
- [ ] Hash-state deep links work: opening `page-type.html#some-id.some-sub-id` expands the matching accordions on load.
- [ ] Filter-driven hiding works: unchecking a phase hides sub-accordions without that tag and collapses out empty large accordions.
- [ ] `search.html` echoes the query in the input and shows results grouped by parent.
- [ ] `admin-queue.html` and `admin-sources.html` are functional rather than pretty (per the brief).
- [ ] Inter variable font is self-hosted under `prototype/assets/fonts/`, not pulled from a CDN.
- [ ] Radix Themes CSS is vendored as a static file, not loaded from a CDN.
- [ ] `prototype/DECISIONS.md` exists (per `DESIGN_HANDOVER.md`) with one bullet per noteworthy decision.

If anything in the checklist fails, send it back to Claude Design rather
than fixing it in the build session — the prototype is a hard input to the
build agent and shouldn't be redesigned downstream.

### Files changed (so far this session)
- `nextstep.md` — added this Session 2 block, ready for Claude Design's commits to land alongside.

---

## Next session — pick up here

Once the prototype is approved, a build session (Claude Code, following
`CLAUDE.md` in this repo) will, roughly in this order:

1. Flask app skeleton at `app.py`; Jinja templates lifted from the prototype.
2. `schema.sql` seeding the three locked taxonomies (`docs/PROJECT.md` §2.1–2.3) and the relational tables in §4.
3. Synonym table populated from the taxonomy synonym columns; search index wired (server-side full-text for bodies, small client-side index for synonym/fuzzy lookups).
4. Admin views: review queue (`/admin/queue`), source management (`/admin/sources`), considerations editor (`/admin/considerations/<slug>`).
5. Ingestion pipeline: RSS poller with ETag caching + content-hash dedup + langdetect (mirror AmuseAlot's `collect_news.py`); structured importers for caniuse, WCAG, MDN BCD, Schema.org.
6. Groq scoring pass (`llama-3.3-70b-versatile`) — never auto-publishes; everything lands in the review queue.
7. Deployment artifacts: `Caddyfile` snippet for `best.amusealot.com`, `bestpractice.service` unit on port 5681, `.env` at `/opt/bestpractice/.env`, daily SQLite backup cron, daily log rotation.
8. `.github/workflows/deploy.yml` on push to `main` — rsync source to VPS + remote `systemctl restart bestpractice`. VPS SSH key added as a GitHub Actions secret.

Before the first deploy: confirm port 5681 is unclaimed on `77.42.40.207`,
confirm Caddy's existing site blocks for `bubble`, `bubblesdontcry-site`,
and `amusealot` are untouched, and add the new site block side-by-side
rather than editing existing ones.
