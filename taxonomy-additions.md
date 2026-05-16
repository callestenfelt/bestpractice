# Taxonomy additions — 2026-05-16

Summary of taxonomy entries added in the 2026-05-16 working session. Totals after this session: **11 phases / 21 page types / 63 components**.

## New page types (4)

| slug | label | definition |
|---|---|---|
| pricing-page | Pricing Page | Plan comparison and price presentation, usually with CTA per tier |
| confirmation-page | Confirmation Page | Post-action page confirming a completed transaction or submission |
| auth-page | Authentication Page | Authentication flow — login, sign-up, password reset |
| 404-page | 404 Page | Page shown when a requested URL doesn't exist, with discovery aids |

## New components (17)

| slug | label | definition |
|---|---|---|
| list | List | Vertical sequence of related items, ordered or unordered |
| textarea | Textarea | Multi-line text input |
| combobox | Combobox | Text input with filterable suggestion list |
| file-upload | File Upload | Input control for selecting and uploading files |
| stepper | Stepper | Multi-step process indicator with per-step navigation |
| code-block | Code Block | Formatted block of code, usually monospaced and syntax-highlighted |
| chart | Chart | Visual representation of data — bars, lines, pies, scatter, etc. |
| cookie-banner | Cookie Banner | Consent UI for cookie or tracking preferences |
| spinner | Spinner | Small indeterminate animated indicator, usually inline |
| loader | Loader | Page or section-level loading state, often blocking with optional message |
| stat | Stat | Single-metric display with value, label, and optional delta |
| rating | Rating | User-facing rating control or display, usually star-based |
| micro-feedback | Micro Feedback | Lightweight feedback prompt for a single binary or short-tap response |
| audio | Audio | Embedded audio player with transport controls |
| map | Map | Embedded geographic map, usually interactive |
| shopping-cart | Shopping Cart | Summary of items selected for purchase, with quantity and price |
| copy-link-button | Copy Link Button | Button that copies a URL or text to the clipboard, usually with confirmation feedback |

## New phase (1)

| slug | label | definition |
|---|---|---|
| legal | Legal | Privacy, terms, consent, accessibility statements, and other regulatory considerations |

## Authoritative source

Canonical taxonomy lives in `docs/PROJECT.md` §2.1 (phases), §2.2 (page types), §2.3 (components). The DB seed (`init_db.py:PHASES` / `PAGE_TYPES` / `COMPONENTS`) is the runtime mirror — kept in lockstep with §2.x by convention. This file is a working-session snapshot, not a source of truth.
