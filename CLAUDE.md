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

Still pending: `/admin/considerations/<slug>` editor, MDN browser-compat-data adapter, per-source-type score threshold, `/admin/sources` UX polish (error display, config_json editor), content-diff for structured sources, cron + daily SQLite backup. See `nextstep.md` Session 13 pointer.

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
