# Consideration scaffolds — status & plan

A **consideration** is the heading users see on a page-type or component view. During approval, each queue item has to land under one (`sub_consideration_placements`). If a destination has no considerations yet, the approval `<select>` is empty and the only way to place an item there is "+ new consideration here" — which means inventing the heading without seeing what already exists.

## Status (2026-05-17)

Seeded via `init_db.py:seed_scaffolds()` from the inline `SCAFFOLDS` list:

| Scope | Destinations | Considerations |
|---|---|---|
| Page types | 21 of 21 | 248 |
| Components | 20 of 63 | 177 |

`site-wide` carries 9 cross-cutting considerations (the contrast/keyboard pair plus security, privacy, performance, error handling, measurement, i18n, and accessible content — the last covering author-time patterns like alt text, captions, transcripts, link text, and plain language) seeded from `SITE_WIDE_SCAFFOLDS`, plus the `ingest-inbox` placeholder.

The stray `Verify group / Inline test ...` row on `article-page` was removed in the same pass (one-shot cleanup in `migrate()`).

`seed_scaffolds()` is idempotent — it inserts only missing `(parent_type, parent_slug, slug)` rows and never overwrites a title or group_label, so an editor-side rename via `/admin/considerations/<slug>` survives a re-seed. Adding a new entry to `SCAFFOLDS` and re-running picks up the addition without disturbing anything else.

## Components not yet covered (43)

The first wave covered 19 components (button, card, cookie-banner, file-upload, footer, form, header, hero, input-field, link, modal, navigation, pagination, search, table, tabs, toast, tooltip, video) plus the pre-existing `image`. The remaining 43 — accordion, alert, audio, avatar, badge, breadcrumb, calendar, carousel, chart, checkbox, chip, code-block, combobox, copy-link-button, date-picker, dropdown-menu, eyebrow, filter, gallery, icon, list, loader, map, menu-bar, micro-feedback, popover, progress-bar, radio-group, rating, scroll-area, select, separator, service-message, shopping-cart, skeleton, slider, sort, spinner, stat, stepper, textarea, toggle, toggle-group — wait for the queue to surface them. The inline "+ new consideration here" handles the long tail.

## Adding more

For a new page-type or component scaffold:

1. Append an entry to `SCAFFOLDS` in `init_db.py` (same shape as existing entries — list of `(group_label, [titles…])`).
2. `python init_db.py` locally; verify with `python query_db.py "SELECT ..."`.
3. Deploy + run `python3 init_db.py` on the VPS.

## What "a scaffold" is (and isn't)

- A scaffold is the **headings only**: `group_label` + `title` per consideration. No sub-considerations attached — those arrive through the approval queue.
- It is **not** editorial content. The job is to predict what umbrella buckets sourced guidance will fall into on each page type, so the approval UI shows a meaningful pick list.
- Use 5–12 considerations per page type, organised into 2–4 `group_label`s (cf. article-page's five groups). Fewer is fine; more becomes noise.

## How to add them

Pattern is already in `init_db.py` — search for `seed_default_data` and the `article-page` / `site-wide` blocks. For each new page type, append a list of dicts with `parent_type`, `parent_slug`, `slug`, `title`, `group_label`, `group_slug`, `group_order`, `display_order`. The function is idempotent (UNIQUE on `parent_type, parent_slug, slug`), so re-running on the VPS picks up additions without duplicating.

Per-page workflow:

1. Draft groups + titles for the page type (markdown list is fine — paste into chat or a scratch file).
2. Add the rows in `init_db.py`.
3. `python init_db.py` locally to verify, then deploy + run on VPS.

## Suggested order

Work through page types in queue-pressure order — whichever destinations the pending items most often want to land on. Quick check:

```sql
SELECT scope_type, scope_slug, COUNT(*) AS pending_hits
FROM pending_items
WHERE status='pending'
GROUP BY scope_type, scope_slug
ORDER BY pending_hits DESC;
```

If that's inconclusive (early days), a reasonable manual order based on likely volume:

1. `landing-page`, `start-page`, `collection-page`, `item-page` — common in any site
2. `checkout-page`, `confirmation-page`, `auth-page`, `profile-page` — transactional core
3. `contact-page`, `about-page`, `faq-page`, `pricing-page` — info pages
4. `search-results-page`, `dashboard-page`, `event-page` — specialised
5. `404-page`, `error-page`, `legal-page`, `cookie-page` — utility / compliance

Components fill in opportunistically as the queue surfaces them.
