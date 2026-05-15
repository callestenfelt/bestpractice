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
- `nextstep.md` — Session 2 block + this deploy-prep sub-section, ready for Claude Design's commits to land alongside.

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
- [ ] `.github/workflows/deploy.yml` triggered on push to `main` — rsync source to `/opt/bestpractice/`, then SSH `systemctl restart bestpractice`. Adapt from bubble's `deploy.yml` (theirs triggers on `master`, ours on `main`; theirs syncs static assets to a webroot, ours syncs a Python app to `/opt/`).
- [ ] Daily SQLite backup cron and log rotation on the VPS.

### Lessons
- Windows' built-in OpenSSH `ssh-keyscan` (in `C:\Windows\System32\OpenSSH\`) is too old for the VPS's modern KEX list. When you need host keys on Windows, pull them from your existing `~/.ssh/known_hosts` instead of running keyscan. Anyone you've previously SSHed to is already a trusted entry.
- Musemaniac is the repo name for what `docs/PROJECT.md` calls "AmuseAlot". Local path: `E:\_dev\musemaniac`. When the briefs reference `collect_news.py`, `score_news.py`, or `run_newsletter.sh`, look there.
- Musemaniac deploys via local `deploy.sh` (scp + ssh systemctl restart), **not** GitHub Actions. Bestpractice will be the first Python-on-VPS project to use GHA-on-push — no existing workflow to copy.

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
