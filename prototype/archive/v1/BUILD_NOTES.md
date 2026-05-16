# BUILD_NOTES.md

Instructions for the build agent (Claude Code), from the design agent.

Read this **after** `PROJECT.md` and `DESIGN_HANDOVER.md`. This document is
specifically about how the prototype in `prototype/` should be wired up, and
what's in the prototype that isn't covered in `PROJECT.md`.

If anything here contradicts `PROJECT.md` — `PROJECT.md` wins, ask the user.

---

## 0. Tl;dr for someone in a hurry

You inherit a static HTML/CSS/JS prototype in `prototype/`. Your job is to
turn it into Flask templates without changing how it looks. You can change
**how** anything is rendered — class names, helper functions, template
inheritance — as long as the rendered DOM and CSS classes survive intact.

Keep these untouched unless you talk to the user:
- The CSS file structure (`tokens.css`, `base.css`, `components.css`) and
  the variable names inside them
- The DOM attribute names listed in §3 (the JS hooks depend on them)
- The accordion hash format in §4
- Every Inter weight / Radix Icon already referenced

Treat the prototype's content (the 15 fake considerations) as throwaway.
Treat its structure as a contract.

---

## 1. File mapping

| Prototype | Flask template |
|---|---|
| `prototype/index.html` | a redirect view to `/page-type/article-page` |
| `prototype/page-type.html` | `templates/page_type.html` |
| `prototype/search.html` | `templates/search.html` |
| `prototype/admin-queue.html` | `templates/admin/queue.html` |
| `prototype/admin-sources.html` | `templates/admin/sources.html` |
| `prototype/styles/*.css` | `static/styles/*.css` — same names |
| `prototype/js/*.js` | `static/js/*.js` — same names |
| `prototype/assets/icons/` | `static/icons/` |
| `prototype/assets/fonts/` | `static/fonts/` |

> **Note on missing `assets/` folder.** The prototype doesn't ship one,
> and that's intentional:
>
> - **Icons.** All icons in the prototype are inline SVGs written directly
>   into the HTML (chevrons, magnifying glass, checkbox tick, status dots).
>   This kept the prototype openable from the filesystem with zero
>   dependencies. The icons used so far are simple geometric strokes, not
>   the Radix Icons set. If you want to switch to Radix Icons during build,
>   replace the inline `<svg>` elements with `<img src="/static/icons/…">`
>   or include the SVG files via Jinja includes. Either is fine. The
>   prototype's inline SVGs are deliberately small and unstyled beyond
>   `stroke="currentColor"`, so swapping them is a search-and-replace job.
> - **Fonts.** The prototype loads Inter from Google Fonts CDN
>   (`fonts.googleapis.com`) so the HTML opens cleanly on the filesystem
>   for design review. Production self-hosts the Inter variable font in
>   `static/fonts/Inter.var.woff2` per `PROJECT.md` §8. Drop the
>   preconnect tags and the Google Fonts `<link>`; add a single
>   `@font-face` declaration to `base.css`.

The prototype loads Inter from Google Fonts CDN for portability. **Self-host
the Inter variable font** in production per `PROJECT.md` §8. Drop the
preconnect tags and the `<link>` to `fonts.googleapis.com` and replace with
a single `@font-face` in `base.css` pointing at `static/fonts/Inter.var.woff2`.

A base template that pulls in the three CSS files, the JS files for the
page, the brand header, and the search input is the obvious extraction.
The prototype is intentionally not DRY across the four files; reduce as
you go.

---

## 2. Component/template breakdown

These four templates are the read surface. The page-type template is the
one that earns most of the work; the others are mostly composition.

### 2.1 page_type.html

The view takes a page-type slug (or component slug, same template) and
emits the considerations belonging to it, grouped by `group_label`.

Pseudocode for the loop:

```python
# in the view
considerations = list_considerations(parent_slug)        # ordered
grouped = group_by(considerations, key='group_label')    # OrderedDict
return render('page_type.html', page=page_type, groups=grouped)
```

In the template, each group is `<section class="group" data-group="{slug}">`.
Each large accordion is `<details class="consideration" id="{slug}">`. Each
sub-accordion is `<details class="sub{is_new}" id="{cons_slug}.{sub_slug}"
data-phases="{phases_joined}">`. See §3 for the full attribute list.

The site-wide group is special. It's rendered as the last group with
`data-group="site-wide"` and `hidden` attribute. The filter JS un-hides it
when the toggle flips. **Don't try to conditionally render it server-side
based on the toggle state** — that breaks the no-JS-required principle and
forces a navigation on every toggle. Render it `hidden` always; client JS
shows it.

### 2.2 search.html

Receives `q` from the query string and emits result groups. Hard parts:

- **Group ordering.** Page types in their `display_order`, then components
  in theirs, then Site-wide last. The prototype's order matches.
- **Snippet generation.** A small window of body text around each match,
  with each match wrapped in `<mark>…</mark>`. Standard half-page Python.
- **Synonym matching.** Use the `synonyms` table to expand the user's query
  before matching. The prototype's hint line ("Includes synonym matches
  for *alternative text*, *image description*") is a literal display of
  which synonyms expanded the query — when none expand, drop the line.
- **Empty state.** Use the prototype's empty markup verbatim. The "try a
  synonym" suggestions list is illustrative — generate three real
  suggestions if you can (closest entries in the synonyms table by
  Levenshtein, or just hardcoded fallbacks for v1).

The "preview: empty state" `<details>` block at the bottom of the prototype
search file exists **only for design review** — drop it in production.

### 2.3 admin/queue.html

Each row is one `sub_consideration` with `status = 'pending'`. Server-side
the form posts to `/admin/queue/{id}/approve|reject|edit`. Each editable
field is its own input/textarea so partial saves are cheap.

Specifics per element:

- **`.editable` textarea.** Auto-saves on blur or after a 1-second
  debounced typing pause. POST to `/admin/queue/{id}` with a partial body.
- **Chip × button.** Removes one phase tag. POST `/admin/queue/{id}/phases`.
- **`+ add phase` chip.** Opens a small popover with the remaining phases
  the item doesn't already have. Vanilla JS, single small file.
- **Association dropdown.** Populated server-side. On change, POST to
  `/admin/queue/{id}/associate`.
- **Approve / Reject buttons.** POST and redirect back to the queue.
- **Edit & approve button.** Opens a `<dialog>` with the full editor
  (one-liner, body textarea, source fields, phases, association). Submit
  flips status to approved and closes.

The relevance-score dot strip (`●●●●●●●○○○ 8/10`) is **invented** by the
design agent and not in `PROJECT.md`. Keep it — it's a useful affordance
at no cost. Render with a small partial that takes a 1–10 integer.

The "Last sync: 2h ago" pill is **invented**. Wire it to the most recent
`sources.last_collected` across all active sources. Format as relative
("just now", "12m ago", "2h ago", "yesterday", or a date if older).

### 2.4 admin/sources.html

Each row is one row from `sources`. The table cells map 1:1 to fields.
The active toggle is a `<form method="post">` wrapping a single checkbox,
with JS submitting on change (or no JS — fall back to a submit button).

**Status colors.** The prototype uses green / amber / red dots for
active / paused / error. This is a deliberate exception to the
"blue accent only" rule in `DESIGN_HANDOVER.md` — system status arguably
needs its own color language. The user has approved keeping them. Don't
extend the green/amber/red use anywhere else.

The "Add source" form posts to `/admin/sources` and reloads the table.
RSS sources require only name + URL; structured sources may need a
`config_json` field — out of scope for v1, the form omits it.

---

## 3. DOM contract — attribute names the JS depends on

Do not change these without also updating the JS.

### Phase filter
- Checkbox inputs: `<input type="checkbox" name="phase" value="{slug}">`
- Site-wide toggle: `<input type="checkbox" id="toggle-sitewide">`
- "Select all" / "clear all" buttons: `data-action="select-all"` / `"clear-all"`

### Sub-accordion filtering
- `<details class="sub" data-phases="seo content ux">` — space-separated
  phase slugs. Empty / missing = "always visible".
- Filter JS hides subs whose phases don't intersect the active set, hides
  considerations whose subs are all hidden, hides group sections whose
  considerations are all hidden.

### Per-consideration item count
- The count text lives in `<span class="consideration__meta"
  data-role="count">`. Filter JS rewrites this to match the visible sub
  count after each filter change.

### "New" marking
- Sub-accordion: `<details class="sub sub--new">`. The class drives the
  left-edge blue stripe.
- Inside the one-liner: `<span class="sub__newdot" aria-hidden="true">`
  followed by `<span class="sr-only">New. </span>` for screen readers.
- A sub is "new" when its `last_updated` is within 14 days of `now()` —
  compute this at render time, not at write time.

### Search form
- `<form class="search-form" action="search.html" method="get">` with an
  `<input type="search" name="q">` inside. The JS upgrades it to a JS
  navigation; the form action is the no-JS fallback. Keep both.

### Search-results query echo
- `<span data-role="query-echo">` is replaced with the query at runtime by
  `search.js`. Server-side, you can render the value directly (e.g.
  `<h1>"{{ q }}"</h1>`) and drop the data-role attribute — your call.

---

## 4. Hash state

The accordion JS reads and writes `location.hash` so deep links work.

**Format.** Comma-separated entries. Each entry is either:

- `cons-slug` — large accordion is open, no specific sub
- `cons-slug.sub-slug` — large accordion is open AND that specific sub
  is open inside it

Example: `#page-title-h1.wcag-246,structured-data`

**On page load.** JS parses the hash and forces `open` on every matching
`<details>` element. Sub IDs include the consideration slug as a prefix
(`<details id="page-title-h1.wcag-246">`) so they're globally unique.

**On every toggle event.** JS rewrites the hash to reflect current open
state.

**Build-agent implementation.** ID format must stay
`{cons_slug}.{sub_slug}`. Slugs are kebab-case per `PROJECT.md` §4.2. If a
sub has no parent (impossible in the data model but worth saying out
loud), there's no two-part ID.

---

## 5. CSS — what's safe to change

### Safe to change
- The values inside `tokens.css`. Swap in vendored Radix Themes here. The
  variable **names** (`--gray-1` … `--gray-12`, `--blue-2` … `--blue-11`)
  are referenced everywhere; either keep the names or do a project-wide
  find-and-replace.
- Adding new utility classes.
- Refactoring `components.css` into smaller files if you prefer.

### Don't change without asking
- The class names listed in §3 (JS hooks).
- The 14-day "new" cutoff. It's design-significant.
- The blue-accent-only rule. Status colors in `admin-sources.html` are the
  one approved exception.
- The 240px rail / 720-800px main column proportions. Density was tuned to
  hit "10–15 collapsed subs visible at 1440px" from
  `DESIGN_HANDOVER.md`.

### Font handling
- Inter, weights 400, 500, 600, 700.
- Variable font preferred; the prototype uses Inter from Google Fonts and
  will switch to a self-hosted variable file. `Inter.var.woff2`.

---

## 6. Inventions in the prototype not covered in PROJECT.md

These elements exist in the prototype but aren't in the project brief.
The user has signed off on keeping them. Don't remove any of them; if
you find yourself unsure how to back them with data, ask.

| Where | What | Implementation notes |
|---|---|---|
| Header search | `⌘K` kbd hint inside input | Visual hint only in v1. Optional: wire `⌘K` / `Ctrl+K` to focus the input. |
| Search results | Per-group "X hits" chip in section header | Just count of results in that group. |
| Search results | "Includes synonym matches for *foo*, *bar*" hint line | Hide when the query didn't expand. Render synonyms in `<em>` (not anchors). |
| Search results | "Site-wide" as a group in results | Group `site-wide` page-type's considerations under this header when relevant. |
| Admin queue | Score dot strip `●●●●●●●○○○ 8/10` | Filled dots = score, empty dots = 10-score. Tooltip "AI relevance score". |
| Admin queue toolbar | "Last sync: 2h ago" pill | Relative time of latest sources.last_collected. |
| Admin queue toolbar | "7 pending · 23 approved this week · 4 rejected" | Three separate counts; "this week" = trailing 7 days. |
| Admin sources | Green / amber / red status dots | Approved exception to blue-only rule. Don't extend. |

---

## 7. Accessibility floor

These must survive every refactor.

- Single H1 per page (the page heading; no second H1 anywhere).
- Landmarks: `<header>` (site), `<main>`, `<aside aria-label="Filters">`,
  `<nav aria-label="Admin">`.
- All interactive elements keyboard-focusable in source order. No positive
  `tabindex`.
- Visible focus rings via `:focus-visible` — already implemented at the
  global level in `base.css`. Don't disable it on any element.
- All icons used decoratively get `aria-hidden="true"`. All meaningful
  icons get a sibling `<span class="sr-only">` label.
- The "new" indicator is paired with an sr-only "New. " text, not color
  alone.
- `prefers-reduced-motion` is honored globally in `base.css`. Don't add
  transitions that bypass it.
- Form inputs all have associated `<label>` elements (either wrapping or
  `for=`).

WCAG target: AA across the board; AAA for body-text contrast.

---

## 8. Deployment integration

Per `PROJECT.md` §7:

- Caddyfile site block for `best.amusealot.com`, port 5681.
- `bestpractice.service` systemd unit.
- `deploy.ps1` PowerShell-friendly deploy script.
- `/opt/bestpractice/data/bestpractice.db` SQLite file.
- Cron-driven daily backup, weekly RSS poll, weekly structured-sync.
- Caddy basic-auth on the whole subdomain.

Templates and static files live under the Flask app root. The deploy
script scp's the app folder; the database stays put on the VPS. Standard
AmuseAlot operational pattern.

---

## 9. Open questions for the user

If you hit any of these, stop and ask:

- **AI scoring threshold.** `PROJECT.md` says "TBD by build agent, start
  at 4". Pick a starting value and surface it as an env variable.
- **Rate limits for Groq.** Mirror AmuseAlot's `score_news.py` behavior.
- **Sources for v1.** Stick to the §5.1 + §5.2 lists. Adrian Roselli is in
  the prototype's sources table as **paused** — it's in §5.3 (future
  sources), so seed it as paused or omit it.
- **The component pages.** `PROJECT.md` lists 40+ components but the
  prototype only renders the Article Page page-type. The component-detail
  template reuses `page_type.html` verbatim with `parent_type =
  component`. Seed at least the components from `DESIGN_HANDOVER.md`'s
  reference list to validate the layout.

---

## 10. What "done" looks like for v1

A single user can:

1. Open `https://best.amusealot.com` (after basic auth), land on a
   page-type view, scroll the considerations.
2. Toggle phase filters and watch the list reshape.
3. Toggle site-wide and see cross-cutting items inline.
4. Search a term; click a result; arrive at the right page with the right
   accordion open via hash.
5. Visit `/admin/queue`, approve/reject AI-scored items, watch the
   read surface pick up newly-approved items with the "new" indicator.
6. Visit `/admin/sources`, pause an active source, watch it stop
   collecting on the next cron tick.
7. Author a new large accordion via `/admin/considerations/<slug>` (out
   of scope for the prototype but in `PROJECT.md` §3.8).

Everything else is v2.
