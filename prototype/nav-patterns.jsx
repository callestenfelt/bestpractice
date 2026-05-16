// nav-patterns.jsx — four navigation patterns for browsing between
// the 17 page types and 47 components in bestpractice.
// Each pattern is a static mockup at ~1320×860 (representative laptop)
// using the existing tokens/base/components stylesheet for fidelity.

const PAGE_TYPES = [
  ['start-page', 'Start Page'],
  ['landing-page', 'Landing Page'],
  ['article-page', 'Article Page'],
  ['collection-page', 'Collection Page'],
  ['item-page', 'Item Page'],
  ['profile-page', 'Profile Page'],
  ['search-results-page', 'Search Results'],
  ['faq-page', 'FAQ Page'],
  ['about-page', 'About Page'],
  ['contact-page', 'Contact Page'],
  ['checkout-page', 'Checkout Page'],
  ['event-page', 'Event Page'],
  ['legal-page', 'Legal Page'],
  ['cookie-page', 'Cookie Page'],
  ['error-page', 'Error Page'],
  ['dashboard-page', 'Dashboard'],
  ['site-wide', 'Site-wide'],
];

const COMPONENTS = [
  'Header', 'Footer', 'Navigation', 'Menu Bar', 'Breadcrumb',
  'Hero', 'Eyebrow', 'Card', 'Button', 'Link',
  'Form', 'Input Field', 'Select', 'Checkbox', 'Radio Group',
  'Toggle', 'Toggle Group', 'Slider', 'Date Picker', 'Modal',
  'Popover', 'Dropdown Menu', 'Tooltip', 'Tabs', 'Accordion',
  'Table', 'Pagination', 'Filter', 'Sort', 'Search',
  'Scroll Area', 'Separator', 'Toast', 'Alert', 'Service Message',
  'Progress Bar', 'Badge', 'Chip', 'Video', 'Image',
  'Icon', 'Carousel', 'Image Gallery', 'Calendar', 'Avatar', 'Skeleton',
];

const PHASES = [
  'Strategy', 'Concept', 'UX', 'Design', 'Frontend',
  'Backend', 'Content', 'SEO', 'Measurement', 'Maintenance',
];

// ─── Small primitives ─────────────────────────────────────────────────

function Chev({ dir = 'right', size = 12 }) {
  const r = { right: 0, down: 90, up: -90, left: 180 }[dir];
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none"
      stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
      style={{ transform: `rotate(${r}deg)`, flex: '0 0 auto' }} aria-hidden="true">
      <polyline points="6,3 11,8 6,13" />
    </svg>
  );
}

function SearchIcon({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none"
      stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true">
      <circle cx="7" cy="7" r="5" />
      <path d="m14 14-3.2-3.2" />
    </svg>
  );
}

function BrandMark() {
  return <span className="site-header__brand-mark" aria-hidden="true" />;
}

// Shared content stub — header + page heading + one open accordion.
// Each pattern renders this in its main column so the comparison is honest.
function MainContent({ width = 720 }) {
  return (
    <div className="main" style={{ maxWidth: width }}>
      <div className="page-heading">
        <div className="page-heading__eyebrow">Page type · <code>Article</code></div>
        <h1 className="page-heading__title" style={{ fontSize: 28 }}>Article Page</h1>
        <p className="page-heading__definition" style={{ fontSize: 14 }}>
          A single piece of editorial content, usually long-form. The reader is here to read; everything else
          either supports that or gets in the way.
        </p>
      </div>
      <hr className="hr" />
      <section className="group">
        <header className="group__header">
          <h2 className="group__title" style={{ fontSize: 18 }}>Before you start</h2>
        </header>
        <div className="consideration" style={{ borderTop: '1px solid var(--gray-5)' }}>
          <div className="consideration__summary" style={{ padding: '14px 16px' }}>
            <span className="consideration__title" style={{ fontSize: 15 }}>Page purpose &amp; audience</span>
            <span className="consideration__meta">3 items</span>
            <Chev />
          </div>
        </div>
        <div className="consideration" style={{ borderTop: '1px solid var(--gray-5)' }}>
          <div className="consideration__summary" style={{ padding: '14px 16px' }}>
            <span className="consideration__title" style={{ fontSize: 15 }}>Editorial brief &amp; angle</span>
            <span className="consideration__meta">3 items</span>
            <Chev />
          </div>
        </div>
        <div className="consideration" style={{ borderTop: '1px solid var(--gray-5)', borderBottom: '1px solid var(--gray-5)' }}>
          <div className="consideration__summary" style={{ padding: '14px 16px' }}>
            <span className="consideration__title" style={{ fontSize: 15 }}>Page title &amp; URL slug</span>
            <span className="consideration__meta">4 items</span>
            <Chev />
          </div>
        </div>
      </section>
      <section className="group" style={{ marginTop: 36 }}>
        <header className="group__header">
          <h2 className="group__title" style={{ fontSize: 18 }}>Top of page</h2>
        </header>
        <div className="consideration" style={{ borderTop: '1px solid var(--gray-5)', borderBottom: '1px solid var(--gray-5)' }}>
          <div className="consideration__summary" style={{ padding: '14px 16px' }}>
            <span className="consideration__title" style={{ fontSize: 15 }}>H1 and document title</span>
            <span className="consideration__meta">
              <span style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: 'var(--blue-9)', marginRight: 6, verticalAlign: 1 }} />
              5 items
            </span>
            <Chev />
          </div>
        </div>
      </section>
    </div>
  );
}

function PhaseFilters({ compact = false }) {
  return (
    <div className="rail__section">
      <div className="rail__heading">
        <span>Filter by phase</span>
        <span className="rail__actions">
          <button className="linkbtn" type="button">all</button>
          <span aria-hidden="true">·</span>
          <button className="linkbtn" type="button">none</button>
        </span>
      </div>
      <ul className="checklist" style={compact ? { fontSize: 13 } : null}>
        {PHASES.map(p => (
          <li key={p}>
            <label className="checklist__item">
              <input type="checkbox" defaultChecked />
              <span>{p}</span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ─── Pattern A: Combined left rail ────────────────────────────────────
function PatternA() {
  return (
    <div style={{ background: 'var(--gray-1)', height: '100%', overflow: 'hidden', fontFamily: 'var(--font-sans)' }}>
      <Header />
      <div className="shell" style={{ paddingTop: 24 }}>
        <aside className="rail" style={{ position: 'static', maxHeight: 'none' }}>
          <div className="rail__section">
            <div className="rail__heading"><span>Browse</span></div>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--gray-10)', margin: '10px 0 4px', fontWeight: 500 }}>
              Page types · 17
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: 13, lineHeight: 1.9 }}>
              {PAGE_TYPES.slice(0, 6).map(([slug, label]) => (
                <RailLink key={slug} label={label} active={slug === 'article-page'} />
              ))}
              <li style={{ color: 'var(--gray-10)', cursor: 'pointer', padding: '2px 8px' }}>Show 11 more…</li>
            </ul>

            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--gray-10)', margin: '14px 0 4px', fontWeight: 500 }}>
              Components · 46
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: 13, lineHeight: 1.9 }}>
              {COMPONENTS.slice(0, 5).map(label => (
                <RailLink key={label} label={label} />
              ))}
              <li style={{ color: 'var(--gray-10)', cursor: 'pointer', padding: '2px 8px' }}>Show 41 more…</li>
            </ul>
          </div>
          <hr className="hr hr--tight" />
          <PhaseFilters />
        </aside>
        <MainContent />
      </div>
    </div>
  );
}

function RailLink({ label, active }) {
  return (
    <li>
      <a href="#" style={{
        display: 'block',
        padding: '2px 8px',
        textDecoration: 'none',
        color: active ? 'var(--gray-12)' : 'var(--gray-11)',
        background: active ? 'var(--gray-3)' : 'transparent',
        borderRadius: 4,
        fontWeight: active ? 500 : 400,
        borderLeft: active ? '2px solid var(--blue-9)' : '2px solid transparent',
        paddingLeft: active ? 6 : 8,
      }}>{label}</a>
    </li>
  );
}

// ─── Pattern B: Three-column (nav + filters + content) ────────────────
function PatternB() {
  return (
    <div style={{ background: 'var(--gray-1)', height: '100%', overflow: 'hidden', fontFamily: 'var(--font-sans)' }}>
      <Header />
      <div style={{
        maxWidth: 1440, margin: '0 auto', padding: '24px 24px 0',
        display: 'grid',
        gridTemplateColumns: '200px 180px minmax(0, 1fr)',
        gap: 32,
      }}>
        <aside style={{ fontSize: 13 }}>
          <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--gray-10)', margin: '0 0 6px', fontWeight: 600 }}>
            Page types
          </div>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, lineHeight: 1.85 }}>
            {PAGE_TYPES.slice(0, 11).map(([slug, label]) => (
              <RailLink key={slug} label={label} active={slug === 'article-page'} />
            ))}
            <li style={{ color: 'var(--gray-10)', padding: '2px 8px' }}>+6 more</li>
          </ul>
          <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--gray-10)', margin: '16px 0 6px', fontWeight: 600 }}>
            Components
          </div>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, lineHeight: 1.85 }}>
            {COMPONENTS.slice(0, 10).map(label => (
              <RailLink key={label} label={label} />
            ))}
            <li style={{ color: 'var(--gray-10)', padding: '2px 8px' }}>+36 more</li>
          </ul>
        </aside>

        <aside style={{ borderLeft: '1px solid var(--gray-5)', paddingLeft: 16 }}>
          <PhaseFilters compact />
          <hr className="hr hr--tight" />
          <label className="toggle-row" style={{ fontSize: 13 }}>
            <input type="checkbox" className="toggle" />
            <span>Show site-wide</span>
          </label>
        </aside>

        <MainContent width={640} />
      </div>
    </div>
  );
}

// ─── Pattern C: Header switcher pill + command palette ────────────────
function PatternC() {
  return (
    <div style={{ background: 'var(--gray-1)', height: '100%', overflow: 'hidden', fontFamily: 'var(--font-sans)', position: 'relative' }}>
      <header className="site-header" style={{ position: 'relative' }}>
        <div className="site-header__inner" style={{ gridTemplateColumns: 'auto 1fr auto', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <a className="site-header__brand" href="#"><BrandMark />bestpractice</a>
            <span style={{ color: 'var(--gray-7)' }}>/</span>
            <button style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '4px 10px 4px 10px', border: '1px solid var(--gray-6)',
              borderRadius: 6, background: 'var(--gray-2)', cursor: 'pointer',
              fontSize: 13, fontWeight: 500, color: 'var(--gray-12)',
              boxShadow: '0 0 0 3px var(--blue-2)',
            }}>
              Article Page
              <span style={{ color: 'var(--gray-10)', fontWeight: 400 }}>·</span>
              <span style={{ color: 'var(--gray-10)', fontWeight: 400, fontSize: 12 }}>page type</span>
              <Chev dir="down" size={11} />
            </button>
          </div>
          <form className="search-form search" role="search" style={{ maxWidth: 320, marginLeft: 'auto', marginRight: 'auto' }}>
            <span className="search__icon" style={{ display: 'flex' }}><SearchIcon /></span>
            <input className="search__input" type="search" placeholder="Search considerations…" />
            <kbd className="search__kbd">⌘K</kbd>
          </form>
          <nav className="site-header__nav">
            <a href="#"><span className="label">Review queue</span></a>
            <a href="#"><span className="label">Sources</span></a>
          </nav>
        </div>
      </header>

      {/* Open palette popover */}
      <div style={{
        position: 'absolute',
        top: 50, left: 168, width: 460,
        background: '#fff',
        border: '1px solid var(--gray-6)',
        borderRadius: 8,
        boxShadow: '0 12px 32px rgba(20, 25, 35, 0.12), 0 2px 6px rgba(20, 25, 35, 0.06)',
        zIndex: 20,
        overflow: 'hidden',
      }}>
        <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--gray-4)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <SearchIcon size={13} />
          <input
            type="text"
            placeholder="Jump to page type or component…"
            defaultValue=""
            style={{ flex: 1, border: 0, outline: 0, background: 'transparent', fontSize: 14 }}
          />
          <kbd style={{ fontSize: 10, padding: '2px 5px', border: '1px solid var(--gray-5)', borderRadius: 3, color: 'var(--gray-10)', background: 'var(--gray-2)' }}>Esc</kbd>
        </div>
        <div style={{ maxHeight: 360, overflow: 'hidden' }}>
          <div style={{ padding: '8px 14px 4px', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--gray-10)', fontWeight: 600, display: 'flex', justifyContent: 'space-between' }}>
            <span>Page types</span><span style={{ fontWeight: 400 }}>17</span>
          </div>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {PAGE_TYPES.slice(0, 5).map(([slug, label], i) => (
              <PaletteRow key={slug} label={label} kind="page type"
                active={slug === 'article-page'}
                highlighted={i === 2} />
            ))}
            <li style={{ padding: '4px 14px 6px', fontSize: 12, color: 'var(--gray-10)' }}>↓ to see all 17</li>
          </ul>
          <div style={{ padding: '8px 14px 4px', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--gray-10)', fontWeight: 600, display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--gray-4)', marginTop: 4 }}>
            <span>Components</span><span style={{ fontWeight: 400 }}>46</span>
          </div>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {['Accordion', 'Button', 'Card', 'Form', 'Modal'].map(label => (
              <PaletteRow key={label} label={label} kind="component" />
            ))}
          </ul>
        </div>
        <div style={{ padding: '6px 14px', borderTop: '1px solid var(--gray-4)', fontSize: 11, color: 'var(--gray-10)', display: 'flex', gap: 14, background: 'var(--gray-2)' }}>
          <span><kbd style={paletteKbd}>↑↓</kbd> navigate</span>
          <span><kbd style={paletteKbd}>⏎</kbd> open</span>
          <span><kbd style={paletteKbd}>Esc</kbd> close</span>
          <span style={{ marginLeft: 'auto' }}>or just search any term ↗</span>
        </div>
      </div>

      <div className="shell" style={{ paddingTop: 24 }}>
        <aside className="rail" style={{ position: 'static', maxHeight: 'none', opacity: 0.55 }}>
          <PhaseFilters />
        </aside>
        <MainContent />
      </div>

      {/* dim overlay */}
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(20,25,35,0.18)', pointerEvents: 'none', zIndex: 15 }} />
    </div>
  );
}

const paletteKbd = {
  fontSize: 10, padding: '1px 4px', border: '1px solid var(--gray-5)',
  borderRadius: 3, background: '#fff', fontFamily: 'var(--font-mono)',
};

function PaletteRow({ label, kind, active, highlighted }) {
  return (
    <li style={{
      padding: '6px 14px',
      display: 'flex', alignItems: 'center', gap: 8,
      fontSize: 13,
      background: highlighted ? 'var(--blue-2)' : 'transparent',
      color: 'var(--gray-12)',
      cursor: 'pointer',
      borderLeft: highlighted ? '2px solid var(--blue-9)' : '2px solid transparent',
    }}>
      <span style={{ fontWeight: active ? 600 : 400 }}>{label}</span>
      {active && <span style={{ fontSize: 10, padding: '1px 5px', border: '1px solid var(--gray-6)', borderRadius: 3, color: 'var(--gray-10)' }}>current</span>}
      <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--gray-10)' }}>{kind}</span>
    </li>
  );
}

// ─── Pattern D: Index / landing page ──────────────────────────────────
function PatternD() {
  return (
    <div style={{ background: 'var(--gray-1)', height: '100%', overflow: 'hidden', fontFamily: 'var(--font-sans)' }}>
      <Header />
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 32px 0' }}>
        <div className="page-heading" style={{ marginBottom: 24 }}>
          <div className="page-heading__eyebrow">References</div>
          <h1 className="page-heading__title" style={{ fontSize: 28 }}>Browse</h1>
          <p className="page-heading__definition" style={{ fontSize: 14 }}>
            Pick a page type or component. Search for a term across all considerations.
          </p>
        </div>

        <hr className="hr" />

        <section style={{ marginBottom: 32 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 12 }}>
            <h2 style={{ fontSize: 14, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--gray-11)' }}>
              Page types
            </h2>
            <span style={{ fontSize: 12, color: 'var(--gray-10)' }}>17</span>
          </div>
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '0 32px', fontSize: 14, lineHeight: 2.1,
          }}>
            {PAGE_TYPES.map(([slug, label]) => (
              <IndexRow key={slug} label={label}
                count={Math.floor(8 + Math.random() * 12)}
                isNew={['article-page', 'item-page'].includes(slug)}
                hot={slug === 'article-page'} />
            ))}
          </div>
        </section>

        <hr className="hr" />

        <section>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 12 }}>
            <h2 style={{ fontSize: 14, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--gray-11)' }}>
              Components
            </h2>
            <span style={{ fontSize: 12, color: 'var(--gray-10)' }}>46</span>
          </div>
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '0 28px', fontSize: 14, lineHeight: 2.1,
          }}>
            {COMPONENTS.slice(0, 28).map(label => (
              <IndexRow key={label} label={label}
                count={Math.floor(3 + Math.random() * 10)}
                isNew={['Card', 'Modal', 'Toast'].includes(label)} />
            ))}
            <div style={{ color: 'var(--gray-10)', fontSize: 13, gridColumn: '1 / -1', paddingTop: 8 }}>
              + 18 more…
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function IndexRow({ label, count, isNew, hot }) {
  return (
    <a href="#" style={{
      display: 'flex', alignItems: 'baseline', justifyContent: 'space-between',
      gap: 8, padding: '2px 0', textDecoration: 'none', color: 'var(--gray-12)',
      borderBottom: '1px dotted transparent',
    }}>
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
        {isNew && <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--blue-9)', display: 'inline-block' }} aria-label="New items" />}
        <span style={{ fontWeight: hot ? 500 : 400 }}>{label}</span>
      </span>
      <span style={{ fontSize: 12, color: 'var(--gray-10)', fontFamily: 'var(--font-mono)' }}>{count}</span>
    </a>
  );
}

// ─── Shared header ────────────────────────────────────────────────────
function Header() {
  return (
    <header className="site-header" style={{ position: 'relative' }}>
      <div className="site-header__inner">
        <a className="site-header__brand" href="#"><BrandMark />bestpractice</a>
        <form className="search-form search" role="search">
          <span className="search__icon" style={{ display: 'flex' }}><SearchIcon /></span>
          <input className="search__input" type="search" placeholder="Search page types, components, considerations…" />
          <kbd className="search__kbd">⌘K</kbd>
        </form>
        <nav className="site-header__nav">
          <a href="#"><span className="label">Review queue</span></a>
          <a href="#"><span className="label">Sources</span></a>
        </nav>
      </div>
    </header>
  );
}

// ─── Notes column ─────────────────────────────────────────────────────
function Notes({ children }) {
  return (
    <div style={{
      width: 280, padding: '16px 20px',
      background: '#fff', border: '1px solid var(--gray-5)',
      borderRadius: 6, fontSize: 13, lineHeight: 1.55,
      color: 'var(--gray-11)', fontFamily: 'var(--font-sans)',
    }}>
      {children}
    </div>
  );
}

// ─── Canvas assembly ──────────────────────────────────────────────────
function App() {
  return (
    <DesignCanvas>
      <DCSection
        id="intro"
        title="How does the user choose between pages?"
        subtitle="There will be 17 page types and 46 components — and every component reuses this same template. Four patterns for getting between them."
      >
        <DCArtboard id="brief" label="The problem" width={520} height={300}>
          <div style={{ padding: 24, fontFamily: 'var(--font-sans)', fontSize: 13, lineHeight: 1.55, color: 'var(--gray-11)', background: '#fff', height: '100%' }}>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--gray-10)', marginBottom: 6, fontWeight: 600 }}>Today</div>
            <p style={{ marginBottom: 14 }}>One template (<code>page-type.html</code>) renders Article Page. The brand link, search, and admin nav exist; <strong>nothing else lets the user jump between page types or components.</strong></p>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--gray-10)', marginBottom: 6, fontWeight: 600 }}>What we're navigating</div>
            <ul style={{ paddingLeft: 18, marginBottom: 14 }}>
              <li><strong>17 page types</strong> · authored once, ordered editorially</li>
              <li><strong>46 components</strong> · same template, different parent</li>
              <li>Plus the one <em>Site-wide</em> bucket already in the rail</li>
            </ul>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--gray-10)', marginBottom: 6, fontWeight: 600 }}>What good looks like</div>
            <p>Single user, daily use, "feels like a wiki crossed with a design-system doc." So: <strong>always-visible</strong> (or always one keystroke away), <strong>scannable</strong>, doesn't fight the dense reading column, doesn't repaint when filters change.</p>
          </div>
        </DCArtboard>

        <DCArtboard id="recommendation" label="My pick" width={520} height={300}>
          <div style={{ padding: 24, fontFamily: 'var(--font-sans)', fontSize: 13, lineHeight: 1.55, color: 'var(--gray-11)', background: 'var(--blue-2)', height: '100%' }}>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--blue-11)', marginBottom: 6, fontWeight: 600 }}>Recommendation</div>
            <p style={{ marginBottom: 12, color: 'var(--gray-12)', fontSize: 14 }}><strong>Pattern A (Combined left rail) + the index page from D as the brand-link destination.</strong></p>
            <p style={{ marginBottom: 10 }}>The rail already exists at 240px and is sticky. Putting <em>Browse</em> above <em>Filter by phase</em> in the same rail costs nothing structurally and matches the Radix docs reference dead-on.</p>
            <p style={{ marginBottom: 10 }}>Show ~6 page types and ~5 components by default, with a "Show more…" that expands inline. Active item gets the existing blue-left-stripe treatment we already use for the "new" indicator's family.</p>
            <p style={{ margin: 0 }}>Brand link goes to <code>/</code> = the index from D. Use it once a week when you want to scan everything.</p>
          </div>
        </DCArtboard>
      </DCSection>

      <DCSection
        id="patterns"
        title="The four patterns"
        subtitle="Each rendered at 1320×860 — what you'd see on a 14″ laptop. Click any artboard to focus."
      >
        <DCArtboard id="pattern-a" label="A · Browse in the existing rail" width={1320} height={860}>
          <PatternA />
        </DCArtboard>

        <DCArtboard id="pattern-b" label="B · Three-column (nav + filters + reading)" width={1320} height={860}>
          <PatternB />
        </DCArtboard>

        <DCArtboard id="pattern-c" label="C · Switcher pill + command palette" width={1320} height={860}>
          <PatternC />
        </DCArtboard>

        <DCArtboard id="pattern-d" label="D · Index landing page" width={1320} height={860}>
          <PatternD />
        </DCArtboard>
      </DCSection>

      <DCSection
        id="tradeoffs"
        title="Trade-offs"
        subtitle="Why I'd pick A; why you might pick something else."
      >
        <DCArtboard id="ta" label="A · Combined rail" width={300} height={360}>
          <TradeOff
            verdict="strong"
            pros={[
              'Zero new layout — the rail is already there.',
              'Always-visible browse, no extra click.',
              'Matches the Radix docs reference faithfully.',
              'Filters stay where they were.',
            ]}
            cons={[
              'Rail gets long. "Show more" hides the tail.',
              'On <960px the rail collapses; browse goes with it.',
            ]}
          />
        </DCArtboard>
        <DCArtboard id="tb" label="B · Three-column" width={300} height={360}>
          <TradeOff
            verdict="medium"
            pros={[
              'Cleanest separation: navigate vs. filter vs. read.',
              'Both lists fit longer without "show more".',
            ]}
            cons={[
              'Eats horizontal space. Reading column drops to ~640px.',
              'Two rails to skim is busier than one.',
              'Brief reserves the rail-width token — adding a column means new tokens & responsive logic.',
            ]}
          />
        </DCArtboard>
        <DCArtboard id="tc" label="C · Switcher pill" width={300} height={360}>
          <TradeOff
            verdict="medium"
            pros={[
              'Scales to 100+ items without taking screen space.',
              'Type-to-jump beats clicking through a list.',
              'Header search + ⌘K already point this way.',
            ]}
            cons={[
              'Hidden by default — less discoverable for a tool you visit daily.',
              'New popover component to build & key-handle.',
              'Doubles up with the existing search; risks confusing "search content" vs. "jump to page".',
            ]}
          />
        </DCArtboard>
        <DCArtboard id="td" label="D · Index landing" width={300} height={360}>
          <TradeOff
            verdict="combo"
            pros={[
              'Calm, scannable, satisfying browse mode.',
              'Per-row counts hint at content density.',
              'Good place for a "new since last visit" affordance.',
            ]}
            cons={[
              'Extra navigation step from index → page.',
              'Doesn\u2019t help once you\u2019re on a page-type view.',
            ]}
            note="Best used as the brand-link destination on top of A or C, not as a standalone solution."
          />
        </DCArtboard>
      </DCSection>
    </DesignCanvas>
  );
}

function TradeOff({ verdict, pros, cons, note }) {
  const badge = {
    strong: { label: 'Recommended', bg: 'var(--blue-2)', fg: 'var(--blue-11)', bd: 'var(--blue-6)' },
    medium: { label: 'Worth considering', bg: 'var(--gray-2)', fg: 'var(--gray-11)', bd: 'var(--gray-6)' },
    combo: { label: 'Pairs with another', bg: '#fff7e0', fg: '#8a6500', bd: '#e6cf80' },
  }[verdict];
  return (
    <div style={{ padding: 18, background: '#fff', height: '100%', fontFamily: 'var(--font-sans)', fontSize: 12.5, lineHeight: 1.55, color: 'var(--gray-11)' }}>
      <span style={{
        display: 'inline-block', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em',
        padding: '2px 7px', borderRadius: 3, background: badge.bg, color: badge.fg,
        border: `1px solid ${badge.bd}`, fontWeight: 600, marginBottom: 12,
      }}>{badge.label}</span>
      <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--gray-10)', marginBottom: 4, fontWeight: 600 }}>Pros</div>
      <ul style={{ paddingLeft: 16, marginBottom: 12 }}>
        {pros.map((p, i) => <li key={i} style={{ marginBottom: 3 }}>{p}</li>)}
      </ul>
      <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--gray-10)', marginBottom: 4, fontWeight: 600 }}>Cons</div>
      <ul style={{ paddingLeft: 16, marginBottom: note ? 12 : 0 }}>
        {cons.map((p, i) => <li key={i} style={{ marginBottom: 3 }}>{p}</li>)}
      </ul>
      {note && (
        <div style={{ borderTop: '1px solid var(--gray-4)', paddingTop: 10, fontStyle: 'italic', color: 'var(--gray-10)' }}>
          {note}
        </div>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
