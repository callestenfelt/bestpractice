# Design handover: bestpractice

You are the design agent. Before reading this document, read `PROJECT.md`
in full. That document is authoritative on what bestpractice does and how
it behaves. This document covers what you produce and the visual direction
you work within.

---

## Your deliverable

A static HTML + CSS prototype of four views. No backend, no build step, no
JavaScript framework — just HTML files in a folder, a stylesheet, vanilla
JS where interactions need it. The build agent will inherit your prototype
and wire it into Flask templates.

### File layout

Produce:

```
prototype/
  index.html               redirects to /page-type/article-page
  page-type.html           the main read view, populated with Article Page
  search.html              search results view
  admin-queue.html         AI review queue
  admin-sources.html       source management
  styles/
    tokens.css             design tokens (built on Radix Themes)
    base.css               typography, layout primitives, resets
    components.css         component styles (accordion, chip, filter, etc.)
  js/
    accordion.js           hash-state persistence, filter-driven hiding
    filters.js             phase filter toggling
    search.js              client-side synonym matching (mocked data is fine)
  assets/
    icons/                 SVGs from Radix Icons as needed
    fonts/                 Inter variable font
```

Each HTML file should be standalone and openable from the filesystem
(no server required). Use realistic but fabricated content for Article
Page — invent 12–18 large accordions across the four groups, each with
3–8 sub-accordions. The content is throwaway; the structure and visual
language are what the build agent will inherit.

---

## Visual direction

### Reference

The primary reference is **radix-ui.com**, specifically the documentation
site (not the marketing pages). It demonstrates:

- A calm, dense information layout suitable for reference reading
- Restrained use of color — near-monochrome with semantic accents
- Generous internal whitespace without wasting screen
- Borders over shadows for depth and grouping
- Tight, scannable typography

You are designing a tool of the same character: a working reference, used
daily by one person, with a lot of dense content. The aesthetic target is
"feels like a wiki crossed with a design system doc." Not a magazine, not
a marketing site, not a dashboard. A reference book.

### Mode

**Light only** for v1. Don't build a dark mode. The build agent will not
implement a toggle.

### Type

**Inter**, self-hosted, variable font. Use the variable axes (weight,
optical size) freely. Base size 14–16px. Generous size contrast between
heading levels.

### Color

Build the palette on **Radix Themes CSS**, included as a vendored
stylesheet. You get their full gray scale and one accent hue out of the box.

The accent is **blue**. Use it sparingly:

- The "new" indicator on sub-accordions updated within 14 days
- Active filter checkboxes
- Focused input outlines
- Hover state on primary links (subtle)

Nowhere else. Decoration and hierarchy come from typography, spacing, and
neutral grays, not from color.

### Spacing and density

Information density is high. The user is scanning a long list of accordions.
Tight vertical rhythm. Generous internal padding inside expanded accordions
so content has room to breathe. The user should be able to see roughly
10–15 collapsed sub-accordions on screen at once on a 1440px display.

### Borders, not shadows

Use hairline borders and subtle background changes for grouping. Avoid
shadow-based elevation. The single exception is the focus ring (use Radix
Themes' default).

### Motion

Minimal. Accordion expand/collapse should feel responsive but not
decorative — a smooth height transition under 200ms. No bouncing, no
staggering, no scroll-linked animation.

---

## The four views

### View 1: Page type (page-type.html)

This is the main read view. The most important view. Populate it with
Article Page content.

**Header.**

- Site title ("bestpractice") at left.
- Centered search input.
- Right: small links to "Review queue" and "Sources." Plain text links,
  no buttons.

**Layout.** Two columns on desktop. Left rail (~240px) for filters; main
column (max-width ~720–800px) for content. Below ~960px viewport, the rail
becomes a top section (probably a collapsible "Filters" disclosure).

**Filter rail.**

- A heading "Filter by phase."
- Ten phase checkboxes, all checked by default. Use the labels from
  PROJECT.md §2.1.
- A separator.
- A single toggle for "Show site-wide considerations." Off by default.
  When on, the considerations from `site-wide` appear inline in the main
  column, grouped under a clearly-labeled "Site-wide" section header at
  the top.

**Main column.**

- Page type label as the page heading. ("Article Page")
- The page type's definition immediately below in muted text.
- A separator.
- Group section headers ("Before you start," "Top of page," etc.) followed
  by their large accordions.
- Considerations in their authored order within each group.

**Large accordion** (collapsed state):

- Title (medium-weight, base size + 1–2 steps).
- Optional small indicator if any sub-accordions are new (a small blue dot
  or count badge).
- Chevron at right indicating expandability.
- Full-width clickable hit area.

**Large accordion** (expanded state):

- Title remains at top.
- Intro paragraph if non-empty. (Most will be empty in v1; design the empty
  state — perhaps no intro at all, no placeholder text.)
- A list of sub-accordions, each as a row.

**Sub-accordion** (collapsed state):

- One-liner text (regular weight).
- A row of metadata: phase tag chips, source name, date.
- The "new" indicator if updated within 14 days (blue treatment — choose:
  small dot to the left of the one-liner, a thin left border, or a "NEW"
  chip).
- Chevron at right.

**Sub-accordion** (expanded state):

- Body text. Paragraphs, lists, occasional inline `code`. No images.
- A footer row: full source attribution, date, "View source" link out.

**Mobile/desktop in body content.** When a sub-accordion's body covers both
viewports, the body has bold inline sub-headers like "**On mobile**" and
"**On desktop**." Treat these as normal heading-like text within the
expanded body; they are not their own accordions.

### View 2: Search (search.html)

User has searched for "alt text" (use this as your example query).

- Header same as main view, with the query echoed in the search input.
- Below header, a small results count ("28 matches in 4 page types and
  6 components").
- Results grouped by parent (page type or component). Within each group,
  the matching large accordion title with a snippet of context (one-liner
  text and a few words around the match, with the match highlighted via
  a subtle background, not bold).
- Clicking a result takes the user to the relevant page-type view with the
  matching accordion auto-expanded (via URL hash).

Empty state: design a clean "no results" with a few helpful suggestions
("try a synonym," "check spelling").

### View 3: Admin review queue (admin-queue.html)

A list of pending sub-accordions awaiting approval.

- Each row shows: the AI-suggested one-liner (in an editable inline field
  styled to look like text by default — outline appears on focus),
  suggested phase tag chips (with × to remove, "+ add" to add more),
  suggested association (dropdown of large accordions across page types
  and components), source attribution, source date, and a longer extract
  paragraph for context.
- Three actions per row: **Approve**, **Edit & approve**, **Reject**.
  "Edit & approve" opens a fuller editor (you can sketch this as a modal
  or as an inline expansion — your call).
- At top, a count and a "clear all rejected" affordance.

This view doesn't need to be beautiful. It needs to be functional and
honor the rest of the design system. The user spends ~15 minutes a week
here. Make it efficient.

### View 4: Source management (admin-sources.html)

A simple table of ingestion sources:

- Name, type (RSS / structured), URL, status, last collected, item count,
  active toggle.
- An "Add source" form below or in a slide-over.

Even simpler than the review queue. Plain. Functional.

---

## Interaction notes

### Accordion behavior

Use the native `<details>` and `<summary>` elements. Style them as
specified. They handle expand/collapse for free. Add JS only for:

1. **URL hash state.** When an accordion opens, update the hash. On page
   load, open accordions whose IDs are in the hash. The build agent will
   handle this properly; you should write a working version for the
   prototype using IDs like `page-title-h1` and
   `page-title-h1.wcag-246`.
2. **Filter-driven hiding.** When phase checkboxes change, hide
   sub-accordions whose tags don't intersect the active set, and hide
   large accordions whose sub-accordions are all hidden.

Both of these are small files under `js/`. Keep them minimal.

### Filter checkboxes

Use real `<input type="checkbox">` styled to match Radix. All ten phases
checked by default. Provide a "select all / clear all" pair of small text
buttons above the checkboxes for convenience.

### Search input

Native `<input type="search">`. No autocomplete dropdown in v1 — when the
user presses Enter or the input is submitted, navigate to `/search?q=...`.
(For the prototype, this just goes to `search.html` with the query in the
URL.)

---

## Accessibility

The tool follows its own rules. Bake in:

- All interactive elements keyboard-operable. Tab order makes sense.
- Visible focus rings everywhere. Use Radix's default focus ring.
- Color contrast WCAG AA at minimum for body text, AAA where easy.
- Reduced-motion media query respected for the accordion expand/collapse.
- All icons have accessible labels. Decorative icons hidden via
  `aria-hidden="true"`.
- The "new" indicator is not color-alone. Pair the blue with a textual or
  shape indicator screen readers can announce.
- Landmark elements: `<header>`, `<nav>` for filters, `<main>` for content,
  `<footer>` if present.

---

## Constraints summary

- Server-renderable HTML. Nothing requires JS to be visible.
- Vanilla JS only, no frameworks. Each JS file under ~100 lines.
- No build step. The prototype must work by opening HTML files directly.
- Radix Themes CSS vendored as a static asset.
- Inter self-hosted.
- Native HTML where it works: `<details>`, `<dialog>`, `<input type="search">`.
- Light mode only.
- Blue accent reserved for "new" + active states. No other use of color.
- Mobile-friendly but desktop-first. The user works on a laptop.

---

## What you decide

Within the constraints above, you decide:

- Exact type scale (sizes, weights, line heights)
- Specific spacing rhythm
- The exact treatment of the "new" indicator
- Microcopy in UI chrome (filter labels, empty states, button labels)
- Icon set within Radix Icons
- Mobile layout adaptations
- Empty-state designs (no results, empty queue, empty source list)
- How filters visually communicate active vs inactive
- Hover and focus states for all interactive elements

---

## What you do not decide

- The taxonomy itself (phases, page types, components — all locked)
- The data model (build agent's territory)
- The behavior of filters, search, accordions, hash state (specified above)
- The pages/views included in the prototype (the four listed are
  authoritative)
- The technology stack
- Whether to use React (no)

---

## Tone of the prototype content

When you fabricate the Article Page considerations, write them in the
voice the tool will eventually have: terse, accurate, no marketing. Bias
the fake sources toward the real source list (NN/g, web.dev, W3C / WCAG,
A11y Project, MDN, caniuse). Real-looking dates. Realistic phase tags.

This matters because the user will judge the design partly through the
density and feel of the content. Authoring 12 hand-feeling considerations
beats authoring 30 obviously-AI ones.

---

## When you're done

Hand back the `prototype/` folder. The user reviews and either approves or
requests changes. Iterate until the user is happy. Once approved, the
prototype becomes a hard input to the build agent: the build agent must
preserve the visual design as-built, only making changes that are required
for the Flask integration to work.

Document any decisions worth flagging in a short `DECISIONS.md` inside the
prototype folder. One bullet per decision. The build agent will read it.
