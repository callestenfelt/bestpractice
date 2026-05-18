# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status

Slice A of the Flask app is shipped and live at `https://best.amusealot.com` (Caddy basic auth, single user). `/page-type/article-page` renders the prototype's considerations from SQLite. The v3 chrome (topbar + collapsible sidebar nav + filters drawer, Phosphor icons) is templated from `prototype/page-type-v3.html` and applies to every route. `/search`, `/admin/queue`, `/admin/sources`, `/component/<slug>` all ship.

**Slice C + D merged to `main` (Sessions 10–11).** The editorial loop is end-to-end:

- RSS ingestion via `collect.py` (4 active feeds: web.dev, A11y Project, NN/g, Google Search Central; 3 deprioritized feeds paused in-DB).
- Structured ingestion via `collect_structured.py` + 5 adapters under `ingestors/`: WCAG 2.2, Schema.org WebPage subtree, caniuse (capped 25/run), OWASP Top 10, GOV.UK Design System. All 5 PROJECT.md §5.1 sources live.
- Groq scoring via `score.py` (`llama-3.3-70b-versatile`, raw HTTP, auto-reject at `<4`).
- `.env` loads `GROQ_API_KEY` via python-dotenv. `requirements.txt` ships feedparser + requests + python-dotenv.

**Session 12 — full-page approval stepper + sub-level placements (merged to `main`).** The editorial UI was rewritten around `/admin/queue/<id>`:

- A sub-consideration is no longer pinned to a single consideration. New `sub_consideration_placements(sub_id, consideration_id, position)` table lets one row appear under different considerations on different page-types / components. Backfilled in `init_db.py:migrate()`; `load_parent_view` reads through it. The `sub_considerations.consideration_id` column remains as the primary placement and FTS join.
- Full-page approval at `GET /admin/queue/<id>` replaces the inline `<dialog>`. Prev/Next stepper, Enter = Approve+Next, page-types + components as checkboxes (each expands to a `<select>` of considerations on that destination grouped by `group_label`).
- `POST /admin/queue/<id>/approve` requires ≥1 placement (validation re-renders with form state preserved); auto-advances to next pending or back to `/admin/queue`. `POST .../reject` flashes an Undo link + auto-advances. `POST .../unreject` flips rejected → pending; same endpoint powers the Re-queue button.
- `/admin/queue?status=rejected` is a Rejected bin alongside Pending; both shown as tabs on the list. `POST /admin/considerations/new` returns JSON for the "+ new consideration here" inline create.
- The category mechanism stays in schema and read path but is **not exposed in the approval UI** — categories had 0 production destinations and the "checkbox expands to pick a consideration" model doesn't fit a multi-page umbrella.
- Templates: `templates/admin/queue_item.html` (new), `templates/admin/_flash.html` (shared flash macro), `templates/admin/queue.html` (rewritten: tabs + card links). JS: `static/js/queue_item.js` (under 100 lines, replaces the deleted `queue.js`).
- Tooling: `query_db.py` is a thin SQLite read helper (refuses mutating SQL unless `--write`). Project-shared `.claude/settings.json` allowlists this project's `python *.py` script invocations + Playwright read-only MCP tools + `sqlite3 *`, and sets `permissions.defaultMode: "acceptEdits"`.

**Consideration scaffolds expanded (2026-05-17).** Empty consideration containers now exist for all 21 page-types and 20 components (image + 19 first-wave: button/card/cookie-banner/file-upload/footer/form/header/hero/input-field/link/modal/navigation/pagination/search/table/tabs/toast/tooltip/video) so the approval `<select>` is never empty on common destinations. Source: `SCAFFOLDS` list in `init_db.py`, seeded via `seed_scaffolds()` (idempotent — never overwrites existing titles, so editor-side renames survive a re-seed). The remaining 43 components stay uncovered; the inline "+ new consideration here" handles long-tail. See `docs/CONSIDERATION_SCAFFOLDS.md`. Prod needs a manual `python3 init_db.py` post-deploy to pick up the 396 new rows + drop the stray `inline-test-...` cleanup row.

Each of the 19 first-wave components also has an **"Accessible content"** consideration appended to its accessibility-flavored group (for cookie-banner, to "Content & choices") so generic content-accessibility guidance — alt text, descriptive link text, plain language, heading hierarchy — has a clear per-component destination alongside the site-wide `sw-accessible-content` umbrella. Slug: `accessible-content`. Re-run `python3 init_db.py` on prod to seed the 19 rows.

Sidebar footer now shows live counts: pending queue items + active sources, rendered with the existing `topbar__toggle-count` badge. Injected via `_inject_nav` in `app.py` (`nav_queue_count`, `nav_sources_count`). `sidebar.js`'s filters-badge selector is scoped to `.topbar .topbar__toggle-count` so it doesn't blank the sidebar counts on routes without a topbar filters toggle.

**Session 13 chrome polish (2026-05-17).** The Placements column on `/admin/queue/<id>` is `position: sticky` and independently scrollable so the one-liner/body/source/phases stay in view while picking destinations. The mobile `filters-scrim` rule is gated with `:has(.filters-rail)` so admin pages without a filters drawer don't get an empty overlay covering the screen.

**Session 14 — content-kind classification (2026-05-17).** Groq now returns a `kind` field alongside `score`; anything not classified `guidance` or `reference` auto-rejects regardless of score. This fixes the failure mode where feature-release blog posts were scoring 7–8 (item #73 "CSS corner-shape" scored 8 pre-change, 2 + `kind=tutorial` post-change). New column `sub_considerations.content_kind TEXT` (migrated in `init_db.py`, added to `schema.sql`). Enum lives in `score.py` only: `KEEP_KINDS = {guidance, reference}`, plus `news / discussion / tutorial / case-study / marketing / other` for the reject path. `score.py --rescore` re-runs Groq on all `status='pending'` rows (one-shot reclassification of the existing queue; safe to interrupt — each row commits before the next, rejected rows fall out of subsequent selects). Rejected items render the kind as a `chip--kind` small-caps badge in `/admin/queue?status=rejected` and on `/admin/queue/<id>`, so the editor can scan-and-requeue any misclassifications. Prod needs `python3 init_db.py` post-deploy to apply the migration, then `python3 score.py --rescore` once to clean up the existing queue.

**Session 14b — AI multi-placement (2026-05-17).** Groq's JSON output replaces the single `consideration_id` field with `placements: [id, ...]` — 0–4 consideration ids cap'd at `MAX_PLACEMENTS = 4` in `score.py`. `apply_result()` clears `sub_consideration_placements` for the row and re-inserts each id (positions 1..N), keeping `sub_considerations.consideration_id` in sync with the first placement so the queue list breadcrumb still works. The approval page at `/admin/queue/<id>` now opens with checkboxes already ticked and the matching `<select>` set on each destination Groq picked — the editor edits a draft set rather than building from scratch. Backward-compat in `validate_result()`: if the model falls back to `consideration_id` instead of `placements`, it's wrapped to a one-element list. Re-run `python3 score.py --rescore` on prod to populate placements for the existing queue (idempotent — safe to run repeatedly).

**Session 15 — edit-in-place link on approved subs (2026-05-18).** Every approved sub on `/page-type/<slug>` and `/component/<slug>` now sports an underlined "Edit" link inside `.sub__metarow` (after the source date), routed at `url_for('admin_queue_item', sub_id=sub.id)`. The link `stopPropagation`s so it doesn't toggle the parent `<details>`. The approval editor at `/admin/queue/<id>` accepts `status='approved'` in addition to `pending`: GET renders the same form pre-filled with current values; POST does the same `DELETE + re-INSERT` against `sub_consideration_placements` / `sub_consideration_phases` it already used for first-time approvals. When `was_approved` the POST handler redirects to the public anchor `/page-type/<parent_slug>#<cons_slug>.<sub_slug>` (or `/component/...`) instead of auto-advancing to the next pending row. Rejected rows still bounce — operator should requeue via the Rejected bin first. In the form template (`templates/admin/queue_item.html`), `is_edit` (set in `_queue_item_context` from `sub.status == 'approved'`) hides the prev/next stepper + position counter, hides the Reject button, swaps the submit label to "Save", and changes the page title to "Edit:". `last_updated` still bumps to `now` on save — a cosmetic re-edit will re-flag the row as "new" for 14 days; worth revisiting if it becomes annoying. No schema change; no prod migration step.

**Session 18 — Approved tab, generic subs-into-scaffolds loader, sw-seo (2026-05-18, deployed).** Three small shipped changes plus one rolled-back experiment:

1. *Approved tab on /admin/queue.* Third tab next to Pending and Rejected, surfacing every approved sub ordered by `last_updated DESC`. Each card carries a single "Edit" button linking to `/admin/queue/<id>` — the queue-side mirror of Session 15's edit-in-place link. No destructive button on the approved card; the existing edit form is the only path to mutate. Required: extending the `admin_queue` route's status guard, adding `approved_count` to `load_queue_view`, treating `status == 'approved'` like pending for the card's `<a>` wrapper, and adding an empty-state branch. Lives in `app.py:723` + `app.py:626-720` + `templates/admin/queue.html`.

2. *Cross-cutting placement spreads.* Direct SQL on prod added 5 placements: alt-text/width-height/lazy-loading rules from article-page also surface on the image component; descriptive-link-text and underline-inline-links rules also surface on the link component. Pending #189 (pagination) and #261 (RealEstateListing schema) were pre-staged onto collection-page so when the editor opens them in the approval form, the destination is already ticked.

3. *`scripts/load_subs_into_scaffolds.py`.* Generic, idempotent, dry-run-default loader that merges a fixture's sub_considerations into existing scaffold rows matched by `(parent_type, parent_slug, slug)`. Insert mode is the default; `--update` overwrites `one_liner`/`body`/`source_*` on existing subs (matched by `consideration_id+slug`). Rebuilds FTS after each apply. Works for any future fixture-into-scaffold merge with verified content.

4. *Rolled-back experiment: Claude-drafted starter fixtures.* `fixtures/collection_page.json` (29 subs) and `fixtures/start_page.json` (24 subs) were drafted from general knowledge and loaded with `source_name="Claude (draft)"` as honest provenance. Editor decided AI-drafted placeholder content isn't the path — even when transparently marked, it dilutes the project's primary-source bias (`PROJECT.md` §9). All 53 subs deleted from both DBs; both fixture JSONs removed from the repo. **Lesson:** future fixtures need real primary sources up front, not "we'll fill them in later" markers. The loader script stays — it's the right tool when the content is right.

5. *`sw-seo` added to site-wide.* New empty consideration in `SITE_WIDE_SCAFFOLDS` (`init_db.py`), display_order=10, intended as the catch-all umbrella for cross-cutting SEO guidance (crawlability, sitemaps, canonicals, hreflang, internal linking, structured data strategy, indexability). Per-page SEO specifics — URL structure, page title & H1, meta description — keep their own dedicated site-wide cons from Session 17.

Prod deploys for the session: each commit auto-deploys via GHA. For the sw-seo addition: `python3 init_db.py` is required on the VPS post-deploy to seed the new row (it's idempotent, no-op on subsequent runs).

**Session 17 — reusable placements + feature-presence scoring (2026-05-18, local only).** Three sequential changes addressed the editor's "I can't put this URL rule on every page" complaint:

1. *Universal cons promoted to site-wide* (`scripts/migrate_universal_to_sitewide.py`). The article-page fixture had originally seeded `url-structure` (id=3), `page-title-h1` (id=5), and `meta-description` (id=14) as page-type-specific considerations. These are genuinely universal — every page has a URL, title, and meta description — so they're now anchored on `(page_type, site-wide)`. The read view's existing site-wide overlay (`app.py` `load_parent_view`, lines 208-224) makes them surface on every page-type with zero extra work. The migration script is idempotent + dry-run by default. The article-page fixture JSON was also updated so a fresh `init_db.py` rebuild lands them in the same place.

2. *Feature-presence category `has-form`* (`init_db.py:1101+`). New `CATEGORY_SCAFFOLDS` list + `seed_category_scaffolds()` helper seeds four form-fundamental considerations (`form-structure`, `form-validation`, `form-autofill`, `form-labels`) attached to the new `has-form` category (auth, checkout, contact, profile-page). Category-owned cons use `parent_type='page_type', parent_slug='category:<slug>'` as a sentinel because the schema CHECK pins `parent_type` to ('page_type','component'); the authoritative destination kind lives in `consideration_destinations(dest_kind='category')`. The read view already JOINed through `page_type_in_category` so members inherit category cons automatically.

3. *Approval UI surfaces site-wide + categories* (`templates/admin/queue_item.html:138-145`, `app.py` `_queue_item_context` + `_cons_by_parent`). The destinations sidebar now renders four sections: "Site-wide (every page)", "Page categories", "Page types", "Components". `_cons_by_parent` now includes `dest_kind='category'` rows. `_dest_keys_for_cons` likewise tracks category placements so editing an approved sub correctly pre-checks its category destination. `POST /admin/considerations/new` accepts `parent_type='category'` and writes the corresponding `consideration_destinations` row.

4. *Groq scoring teaches feature-presence* (`score.py`). The catalog tags each cons with `[SITE-WIDE]`, `[CAT:<slug>]`, or its parent label so the model can see destination class at a glance. A category cheat-sheet (slug + label + member page-types) is appended to each user prompt. The system prompt's placements section was rewritten around a three-step reason-about-scope flow: universal → [SITE-WIDE], categorical → [CAT:*], specific → page-type/component. Concrete forbidden patterns are spelled out ("never enumerate page-types for URL/title/heading rules"). Smoke-tested: WCAG 2.4.2 page-titles routed to cons 5 ([SITE-WIDE] Page title & H1); "Use fieldset to group form inputs" routed to cons 474 ([CAT:has-form] Form structure & fieldsets).

Prod deploy steps (do once): `python3 init_db.py` (new category + 4 cons), `python3 scripts/migrate_universal_to_sitewide.py --apply` (moves 3 article-page cons → site-wide), optional `python3 score.py --rescore` to recompute placements on the existing pending queue against the new catalog. No schema migrations beyond rows added to existing tables.

**Session 16 — daily SQLite backup via systemd timer (2026-05-18, installed and running).** `scripts/backup_db.sh` snapshots `/opt/bestpractice/data/bestpractice.db` to `/var/backups/bestpractice/bestpractice-<UTC-stamp>.db.gz` once a day, then prunes anything older than 14 days. Uses `sqlite3 .backup` (lock-safe, no need to stop the Flask service) + `PRAGMA integrity_check` smoke test + atomic rename + gzip. Fires from `bestpractice-backup.timer` at 03:17 UTC daily (`Persistent=true` catches missed runs). Service runs as root since the DB is root-owned; `Nice=10` + `IOSchedulingClass=idle` keep it polite. First snapshot already captured (`bestpractice-20260518T063459Z.db.gz`). Override paths via env vars (`BESTPRACTICE_DB`, `BESTPRACTICE_BACKUP_DIR`, `BESTPRACTICE_BACKUP_RETAIN_DAYS`) if needed. The `sqlite3` CLI is now installed via a new GHA workflow step (`apt-get install -y sqlite3`) — Slice A never required it, only Python's stdlib `sqlite3` module + `libsqlite3-0`, so a fresh VPS provisioning previously left the CLI missing and `backup_db.sh` would fail on `sqlite3: command not found` until manually installed. Idempotent, sub-second no-op on every subsequent deploy. Re-installation steps for a fresh VPS rebuild are preserved in `nextstep.md` Session 16 (`cp .../bestpractice-backup.{service,timer} /etc/systemd/system/` + `systemctl daemon-reload` + `systemctl enable --now bestpractice-backup.timer`).

**Session 20b — approval UI relabel (2026-05-18, deployed).** Follow-up to Session 20: the queue/approval form had two destination blocks that both said "every page" in spirit ("Site-wide (every page)" and "All pages" under Page categories) with different render semantics. Renamed the first block to "Cross-cutting umbrellas" and added a one-line hint under each destination heading: umbrellas → trailing bucket at the bottom; categories → inline in the page's natural group, with `All pages` covering every page-type (URL, title, meta, SEO). Pure template + CSS change (`templates/admin/queue_item.html`, `static/styles/components.css` — new `.qitem__dest-hint` rule). No data migration. The `dest_group` Jinja macro now takes an optional `hint` arg.

**Session 20 — `all-pages` category, universals render inline, site-wide off components (2026-05-18, deployed).** The site-wide mechanism was overloaded: a page_type row, a destination class, AND a hardcoded render bucket that forced `group_label='Site-wide considerations'` / `group_order=999` on every cons attached to it. Three consequences fixed this session:

1. *Per-page universals were buried at the bottom of every page render*, even though their natural home is "Before you start" (URL structure), "Top of page" (Page title & H1), or "Behind the scenes" (Meta description, SEO).
2. *The site-wide overlay leaked onto `/component/<slug>` renders.* Components were getting URL structure / Page title / Meta description / SEO and the 9 umbrellas on top of their own cons. Components describe buttons and modals, not pages — that overlay was unintended.
3. *Spreading a cons (e.g. "eyebrow") to every page-type meant ticking 20 destination checkboxes one at a time*, or scaffolding empty cons on every page-type first.

The fix introduces an `all-pages` built-in page_type_category whose members are all 20 real page-types (everything except the synthetic `site-wide`). Per-page universals get moved from `(page_type, site-wide)` → `(category, all-pages)`. Category-destined cons already render *inline* via `load_parent_view`'s existing category JOIN (Session 17) — they appear in their own declared group/order, not the trailing 999 bucket. Four cons migrated: `url-structure` (→ "Before you start" / order 1.3), `page-title-h1` (→ "Top of page" / 2.1), `meta-description` (→ "Behind the scenes" / 5.1), `sw-seo` (→ "Behind the scenes" / 5.4). The 9 remaining umbrellas (Performance, Security, Privacy, Keyboard nav, Contrast, Accessible content, Error handling, i18n, Measurement) stay anchored on `site-wide` and still render as the trailing bucket — they're cross-cutting umbrellas without a natural per-page home.

Files touched:
- `init_db.py` — `all-pages` added to `PAGE_TYPE_CATEGORIES` (at the top so display_order=1).
- `scripts/migrate_universals_to_all_pages.py` — idempotent, dry-run-default migration. Updates `parent_slug` to `category:all-pages`, sets natural group_label/slug/order/display_order, swaps the row in `consideration_destinations` from `(page_type, site-wide)` to `(category, all-pages)`.
- `app.py` — site-wide overlay block gated on `parent_type=='page_type'` so components no longer pick it up. New comment block explains the split (category vs umbrella).
- `score.py` — system prompt's placement guidance rewritten around the new split: per-page universals (URL, page title, meta description, SEO basics) go to `[CAT:all-pages]`; cross-cutting umbrellas (performance, security, privacy, accessibility umbrellas, error handling, measurement, i18n) go to `[SITE-WIDE]`. The trailing reminder in the user prompt was updated to match. The catalog tagging in `fetch_consideration_catalog` already handles `[CAT:all-pages]` automatically — no code change there.

Editorial workflow change: to fan a cons to every page (e.g. "Eyebrow / kicker"), the editor now ticks "All pages" in the approval form's "Page categories" section — one click instead of 20.

Prod deploy steps (do once, in this order): `python3 init_db.py` (seeds the new category + 20 memberships), then `python3 scripts/migrate_universals_to_all_pages.py --apply` (moves the 4 cons). Both are idempotent. No schema change. Optional `python3 score.py --rescore` afterwards to let Groq re-route any pending items that should have hit `[CAT:all-pages]` but currently sit on `[SITE-WIDE]` placements.

**Session 19 — one_liner collision guard in score.py (2026-05-18, deployed).** Groq's rewrite step occasionally summarized two distinct source URLs down to the same `one_liner` (e.g. WCAG 1.2.3 and 1.2.5 both became "Prerecorded video requires audio description"). Ingest-path dedup (`collect.py` URL-set check + structured-path `UNIQUE(consideration_id, slug)`) is fine — the collisions were post-score artifacts. New guard at the top of `apply_result` in `score.py`: before writing, query for any other `sub_considerations` row with case-insensitive matching `one_liner` AND a different `source_url`; on hit, fall back to the row's original `source_title` (truncated to 240 chars) and log `one_liner collision with #<id>` to stdout. The check spans all statuses, so a new pending row won't collide with an existing approved/rejected sibling. `apply_result` signature changed from `(conn, item_id, parsed, threshold)` → `(conn, item, parsed, threshold)` so the guard has `source_url` + `source_title` without a second SELECT. Retroactively cleaned up local DB's 3 collisions (#301, #283, #69) via direct SQL — chose this over `--rescore` because rescore only touches `status='pending'` (would have re-classified ~230 unrelated rows to maybe fix one of three pairs). Prod has its own ingested corpus; post-deploy check on the VPS: `python3 query_db.py "SELECT one_liner, COUNT(*) c, GROUP_CONCAT(id) ids FROM sub_considerations WHERE one_liner <> '' GROUP BY LOWER(one_liner) HAVING c > 1"` and apply the same UPDATE for any sibling rows found. No schema change.

**Session 21 — queue source filter (2026-05-18, deployed).** Added a chip-style source filter above the queue list and threaded it through the full approval flow. Chips render only when a tab has ≥2 distinct `source_name` values; all-ticked = no filter, ticking off hides cards client-side. State is mirrored to the URL as repeated `?sources=A&sources=B` via `history.replaceState` (so reload/back-nav persist and URLs are shareable), and JS rewrites every `a[href^="/admin/queue/"]` and `form[action^="/admin/queue/"]` inside each `.qcard` so the sidebar Open/Edit/Reject/Re-queue actions carry the filter into the next request. Server side: `_pending_queue_ids` gained an optional `sources` arg → `WHERE source_name IN (...)`, and a new `_active_sources()` helper reads `request.values.getlist('sources')` so it works on both GET and POST. The approve form ships hidden `<input name="sources">` inputs (same form is reused for in-item Reject via `form.action` swap), and approve/reject redirects propagate `?sources=` to the next item. The item header shows "Filtering by source: X · Clear" (chip rendered with the reserved blue accent — active-filter state is one of blue's allowed uses). Three commits across the session, including a specificity fix (`.qcard { display: grid }` outranks UA `[hidden] { display: none }`, so an explicit `.qcard[hidden] { display: none }` rule was needed) and a follow-up rewriting per-card form actions (the first cut only rewrote `.qcard__link` and missed the sidebar Reject form). Files: `static/js/queue_filter.js` (new), `templates/admin/queue.html`, `templates/admin/queue_item.html`, `static/styles/components.css`, `app.py`. No schema change; pure GHA rsync deploy. Tab-link propagation of `?sources=` is the next nicety — switching tabs currently resets chips to all-ticked.

Still pending: `/admin/considerations/<slug>` editor, MDN browser-compat-data adapter, per-source-type score threshold, `/admin/sources` UX polish (error display, config_json editor), content-diff for structured sources, queue tab-link source-filter propagation. See `nextstep.md` Session 21 pointer.

The GHA workflow at `.github/workflows/deploy.yml` rsyncs to `root@77.42.40.207:/opt/bestpractice/` and restarts `bestpractice.service` on every push to `main` (excluding doc-only paths). Schema changes still need a manual `python3 init_db.py` on the VPS post-deploy. One-time provisioning already done on prod: `GROQ_API_KEY` + `BESTPRACTICE_SECRET` are in `/opt/bestpractice/.env`, and `requirements.txt` was pip-installed when Slice C+D deployed. Local dev falls back to `BESTPRACTICE_SECRET="dev-only-not-secret"` if the env var is unset.

The prototype remains a hard input — canonical file is `prototype/page-type-v3.html`. Visual decisions live in `prototype/DECISIONS.md` and `prototype/BUILD_NOTES.md`. Older prototype iterations live in `prototype/archive/v1/` for reference but are not the source of truth. Don't redesign; wire it up.

**VPS Python note.** The VPS runs Python 3.10.12, not the 3.12+ that `PROJECT.md` §8 specifies. Slice A doesn't trip on this; flag if you reach for 3.12-only syntax.

## Running it locally

```
pip install -r requirements.txt    # one-time, installs feedparser/requests/dotenv
python init_db.py                  # one-time, creates data/bestpractice.db (idempotent)
python app.py                      # serves on http://localhost:5681
```

For the ingestion pipeline (after putting `GROQ_API_KEY` in `.env`):

```
python collect.py             # RSS sources → pending rows
python collect_structured.py  # WCAG / Schema.org / caniuse / OWASP / GOV.UK → pending rows
python score.py               # Groq-score pending rows (auto-reject below 4)
```

`init_db.py` is idempotent. `app.py` exits with a clear message if the DB file is missing.

## Authoritative documents

Read these before doing any work. They are the source of truth and override any assumptions you might make from the codebase or general best practices:

- `docs/PROJECT.md` — what bestpractice is, vocabulary, data model, ingestion pipeline, deployment, editorial principles, non-goals. **Both agents read this in full.**
- `docs/DESIGN_HANDOVER.md` — what the design agent produces (prototype layout, visual direction, the four views, interaction notes). Visual decisions live here.

A `BUILD_HANDOVER.md` is referenced in `PROJECT.md` but does not yet exist — implementation decisions will land there when the build stage begins.

## Domain model essentials

The product is a personal reference tool organized by **page type and component** (the inversion: not by discipline). Three taxonomies seed the database — do not invent new entries autonomously; additions require explicit user approval:

- **Phases** (11, filterable): strategy, concept, ux, design, frontend, backend, content, seo, measurement, maintenance, legal. See `PROJECT.md` §2.1.
- **Page types** (21, including the special `site-wide` bucket). See §2.2.
- **Components** (~63). See §2.3.

Content is structured as **considerations** (large accordions, scoped to a page type or component) containing **sub-considerations** (sub-accordions, each a single sourced piece of guidance with phase tags, source, date, body). The data model is in §4.

`site-wide` is not a real page — it's cross-cutting considerations that can be layered onto any page-type view via a toggle.

A sub-consideration may have **zero** phase tags; this means "applies to all phases" and it is always visible regardless of filter state.

## Hard constraints (do not violate without explicit user approval)

These are spelled out across the briefs; collecting the ones easiest to forget:

- **Stack:** Python 3.12+, Flask, Jinja2, SQLite (stdlib `sqlite3`, not SQLAlchemy). Server-rendered HTML, vanilla JS, **no build step, no bundler, no npm, no React/Vue/Svelte**. Radix Themes CSS as a vendored stylesheet. Inter self-hosted. See `PROJECT.md` §8.
- **Native HTML first:** `<details>`/`<summary>` for accordions, `<dialog>` for modals, `<input type="search">` for search. Per-feature JS files under `static/js/`, each <100 lines.
- **Light mode only** for v1. No dark-mode toggle.
- **Blue is reserved.** The blue accent means exactly two things: the "new" indicator (sub-accordions whose `last_updated` is within 14 days) and active filter/focus states. Do not use blue anywhere else.
- **Never auto-publish ingested items.** Groq/Llama scoring lands items in the review queue with status `pending`; the user approves manually. This is the whole point of the tool.
- **No auto-overwrite of guidance.** When new guidance supersedes old, the user sets `superseded_by` manually. Old items stay in the DB and are hidden from read views.
- **Soft-delete only** for user-authored content (via `status` field).
- **Deployment is PowerShell-friendly** (no WSL on the dev machine). Same VPS as AmuseAlot, port 5681, Caddy basic auth at the proxy. See §7.

## Out of scope for v1

Public access, multi-user, comments/social, native app, dark mode, image hosting, sub-accordion edit history, i18n, public API, newsletter. See `PROJECT.md` §10. Don't add scaffolding for these "just in case."

## Editorial voice when fabricating or summarizing content

Terse, accurate, no marketing language. Bias toward primary sources (specs, standards, research) over commentary. A WCAG success criterion beats a blog post about WCAG. Tag honestly — don't over-tag to inflate visibility. See §9.

## Conventions

- Slugs are kebab-case and URL-safe.
- Datetimes are UTC ISO 8601.
- The accordion deep-link hash format is `/page-type/<slug>#<consideration-id>.<sub-consideration-id>` (e.g. `/page-type/article-page#h1-and-title.wcag-246`).
- Group ordering on a page type comes from `group_label` + `group_order` on each consideration — it is data, not hardcoded layout.

## Reference: AmuseAlot

`PROJECT.md` references a sibling project, AmuseAlot, as the pattern for RSS ingestion (`collect_news.py`: ETag caching, content-hash dedup, langdetect), Groq scoring (`score_news.py`: retry behavior, rate limiting, prompt structure), env loading (`run_newsletter.sh`), and deployment. AmuseAlot is **not in this repo** — if you need to consult it, ask the user for the path.
