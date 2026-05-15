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

## Next session — Session 3 (build) starts here

Prototype is approved and committed. The next session is the **build
agent** per `CLAUDE.md`. Hard inputs: `docs/PROJECT.md`,
`docs/DESIGN_HANDOVER.md`, `prototype/BUILD_NOTES.md`,
`prototype/DECISIONS.md`. Don't redesign — wire it up.

Rough order:

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
