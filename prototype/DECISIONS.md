# DECISIONS.md

Design decisions worth flagging for the build agent. Everything not listed
here is either obvious from the prototype or covered in PROJECT.md / DESIGN_HANDOVER.md.

## Tokens

- `prototype/styles/tokens.css` defines an **original** 12-step gray scale and
  a 6-step blue scale, in the spirit of the brief's "calm / near-monochrome
  / borders-over-shadows" reference. They are NOT verbatim copies of any
  third-party token set. The variable names follow the conventional `--gray-N`
  / `--blue-N` shape, so swapping them for vendored Radix Themes CSS at build
  time is a find-and-replace exercise.
- If you choose to vendor Radix Themes verbatim, drop in their stylesheet,
  delete `tokens.css`, and update the variable names in `base.css` /
  `components.css` (`--gray-X` → `var(--gray-a11)` etc.). The prototype's
  visual character should survive that swap.

## Typography

- Inter is loaded from Google Fonts in the prototype for portability. The
  build agent self-hosts the variable font from `static/fonts/` per the brief.
- Base size 15px (the brief said 14–16). At desktop reading distance it sits
  between density and breathing room.
- `text-wrap: pretty` on body paragraphs, `text-wrap: balance` on H1.

## The "new" indicator

Chose a **6px solid blue dot** to the left of the one-liner, paired with a
2px-wide blue stripe on the sub-accordion's left edge (`.sub--new::before`).
Two reasons: the dot is scannable in a long list; the stripe is the strong
signal when the user is already inside an expanded large accordion. A
visually-hidden "New. " span makes it announce for screen readers.

The cutoff is editorial, not behavioural — the prototype shows three subs
flagged new. In production the server stamps `--new` when `last_updated`
is within 14 days.

## Phase chips

Phase chips are monochrome (single gray fill). The brief reserves color for
"new" and active states; per-phase color would dilute that. The chip's only
job is to be scannable and filterable. If you find users want stronger
phase identification, that's a separate decision the user can make later.

## Blue accent — definitive list

`DESIGN_HANDOVER.md` reserves blue for the "new" indicator, active filter
checkboxes, focused input outlines, and subtle link hover. The prototype
also uses blue for two close cousins. The complete list of approved blue
uses, for the build agent's reference:

1. The "new" indicator on sub-accordions (dot, left-edge stripe, meta text)
2. Filter checkboxes when `:checked`
3. The site-wide toggle when `:checked`
4. `:focus-visible` rings on all inputs, textareas, buttons
5. Link hover — body links, result-row titles, footer source links
6. `<mark>` background for search-hit highlights (`--blue-2` tint, `--blue-11` text)
7. `.results-meta em` for synonym-name highlights, same tint as `<mark>`
8. The Phosphor icon on `.sidebar__link[aria-current="page"]` (v3 handover §3.8) — same `--blue-11` as the active-link border-left stripe

Don't add a ninth without checking. A `.chip--blue` utility class once
existed for status-flagged chips; it was unused and has been removed. Add
it back only with a concrete use case the user has approved.

## Accordion behaviour

- Native `<details>`/`<summary>`. The expand affordance is a 16px chevron
  that rotates 90° on open.
- `accordion.js` reads and writes the URL hash. Two-level encoding: a
  hash entry is either `top-id` (expand the large accordion only) or
  `top-id.sub-id` (expand both).
- The build agent should preserve the hash format. Existing IDs in
  `page-type.html` are illustrative; the production IDs will come from the
  database slug.
- Multiple sub-accordions and large accordions can be open simultaneously.

## Filters

- Phase checkboxes write to the DOM only; no URL state in v1. If the user
  wants shareable filtered views later, encode the *off* phases in the
  query string (`?off=seo,measurement`) — the default-all state has no URL.
- "select all / none" pair under the rail heading.
- Site-wide considerations live in their own group with `hidden` by default;
  toggling adds them inline at the top of the main column.
- Empty large accordions and empty group headers hide entirely; no greyed-
  out shells.

## Header search

- Submits to `search.html?q=...`. No autocomplete in v1 per brief.
- `⌘K` hint in the input is visual-only in the prototype (no keyboard
  handler). Build agent may wire it up if cheap.

## Admin queue

- The one-liner is an inline `<textarea class="editable">` that looks like
  body text until focused (border + background appear on `:hover` / `:focus`).
- AI relevance score is a 10-dot visualisation in the source row. Cheap to
  parse at a glance; doesn't waste space on a labelled scale.
- "Edit & approve" is sketched as a separate button, distinct from "Approve".
  Build agent: open a modal or expand inline — the user has no opinion yet.

## Admin sources

- The form is below the table, intentionally simple. The brief said
  "doesn't need to be pretty, just functional"; I held to that.
- Status pills use semantic dots, not coloured pills, to avoid invoking the
  blue accent outside its reserved meanings.
- Last-collected timestamps include a HH:MM so the user can correlate with
  cron schedule when debugging.

## Responsive strategy

- Below 960px the filter rail collapses to a top section; main column
  takes full width. The rail isn't wrapped in a `<details>` in the
  prototype (always visible at any width), but production should disclose
  it on mobile per the brief.
- Below 720px the queue cards and the source form collapse to single-column.

## Accessibility checklist (the prototype's own compliance)

- Single H1 per page.
- Landmarks: `<header>`, `<main>`, `<aside>` (filter rail), `<nav>` (header
  admin links).
- `:focus-visible` on every interactive element. Focus ring inherits from
  the blue accent.
- "New" indicator pairs blue dot with sr-only "New. " text.
- Form labels associated via `<label for>` or wrapped.
- Reduced-motion media query disables transitions globally.
- Native form controls (checkbox, toggle, search) keep keyboard semantics.

## Out of scope / known gaps

- No service-worker / offline shell — admin tool, single user, not needed.
- No light/dark toggle.
- No print stylesheet. Could be a one-evening add.
- No `<dialog>` modal yet; "Edit & approve" stub doesn't open anything.
- Search is mocked content — no real indexing.
