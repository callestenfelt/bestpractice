# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status

The design prototype is approved and canonical at `prototype/`, and the build agent has shipped Slice A of the Flask app: `app.py` + `schema.sql` + `init_db.py` + `templates/` + `static/`, with the prototype's 18 Article Page considerations / 59 sub-accordions imported as fixtures. `/page-type/article-page` renders identically to the prototype, served from SQLite.

Slices B+ are still pending: `/search`, the three admin views (`/admin/queue`, `/admin/sources`, `/admin/considerations/<slug>`), the `/component/<slug>` route, other page types, RSS + structured ingestion, and Groq scoring. See `nextstep.md` for the running session log and the current "Next session" pointer.

The prototype remains a hard input — visual decisions live in `prototype/DECISIONS.md` and `prototype/BUILD_NOTES.md`. Don't redesign; wire it up.

## Running it locally

```
python init_db.py     # one-time, creates data/bestpractice.db
python app.py         # serves on http://localhost:5681
```

`init_db.py` is idempotent. `app.py` exits with a clear message if the DB file is missing.

## Authoritative documents

Read these before doing any work. They are the source of truth and override any assumptions you might make from the codebase or general best practices:

- `docs/PROJECT.md` — what bestpractice is, vocabulary, data model, ingestion pipeline, deployment, editorial principles, non-goals. **Both agents read this in full.**
- `docs/DESIGN_HANDOVER.md` — what the design agent produces (prototype layout, visual direction, the four views, interaction notes). Visual decisions live here.

A `BUILD_HANDOVER.md` is referenced in `PROJECT.md` but does not yet exist — implementation decisions will land there when the build stage begins.

## Domain model essentials

The product is a personal reference tool organized by **page type and component** (the inversion: not by discipline). Three taxonomies are locked and seed the database — do not invent new entries:

- **Phases** (10, filterable): strategy, concept, ux, design, frontend, backend, content, seo, measurement, maintenance. See `PROJECT.md` §2.1.
- **Page types** (17, including the special `site-wide` bucket). See §2.2.
- **Components** (~45). See §2.3.

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
