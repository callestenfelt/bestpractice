-- bestpractice schema. PROJECT.md §4.
-- SQLite, stdlib sqlite3. Datetimes as TEXT ISO 8601 UTC.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS phases (
  slug          TEXT PRIMARY KEY,
  label         TEXT NOT NULL,
  definition    TEXT NOT NULL DEFAULT '',
  display_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS page_types (
  slug            TEXT PRIMARY KEY,
  label           TEXT NOT NULL,
  definition      TEXT NOT NULL DEFAULT '',
  schema_org_type TEXT,
  icon            TEXT,
  display_order   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS components (
  slug          TEXT PRIMARY KEY,
  label         TEXT NOT NULL,
  definition    TEXT NOT NULL DEFAULT '',
  icon          TEXT,
  display_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS synonyms (
  id          INTEGER PRIMARY KEY,
  entity_type TEXT NOT NULL CHECK (entity_type IN ('phase','page_type','component')),
  entity_slug TEXT NOT NULL,
  synonym     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_synonyms_lookup ON synonyms(entity_type, entity_slug);
CREATE INDEX IF NOT EXISTS idx_synonyms_text   ON synonyms(synonym);

CREATE TABLE IF NOT EXISTS considerations (
  id            INTEGER PRIMARY KEY,
  slug          TEXT NOT NULL,
  parent_type   TEXT NOT NULL CHECK (parent_type IN ('page_type','component')),
  parent_slug   TEXT NOT NULL,
  title         TEXT NOT NULL,
  intro         TEXT NOT NULL DEFAULT '',
  group_label   TEXT NOT NULL DEFAULT '',
  group_slug    TEXT NOT NULL DEFAULT '',
  group_order   INTEGER NOT NULL DEFAULT 0,
  display_order INTEGER NOT NULL DEFAULT 0,
  status        TEXT NOT NULL DEFAULT 'approved' CHECK (status IN ('approved','draft','deleted')),
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL,
  UNIQUE (parent_type, parent_slug, slug)
);
CREATE INDEX IF NOT EXISTS idx_considerations_parent ON considerations(parent_type, parent_slug);

CREATE TABLE IF NOT EXISTS sub_considerations (
  id               INTEGER PRIMARY KEY,
  consideration_id INTEGER NOT NULL REFERENCES considerations(id) ON DELETE CASCADE,
  slug             TEXT NOT NULL,
  one_liner        TEXT NOT NULL,
  body             TEXT NOT NULL DEFAULT '',
  source_name      TEXT NOT NULL DEFAULT '',
  source_suffix    TEXT NOT NULL DEFAULT '',
  source_title     TEXT NOT NULL DEFAULT '',
  source_url       TEXT NOT NULL DEFAULT '',
  source_date      TEXT,
  status           TEXT NOT NULL DEFAULT 'approved' CHECK (status IN ('pending','approved','rejected')),
  display_order    INTEGER NOT NULL DEFAULT 0,
  created_at       TEXT NOT NULL,
  last_updated     TEXT NOT NULL,
  superseded_by    INTEGER REFERENCES sub_considerations(id),
  -- 1-10 from Groq scoring; NULL for items that didn't enter via the queue.
  relevance_score  INTEGER,
  -- Groq classification: guidance|reference (KEEP) or news|discussion|tutorial|
  -- case-study|marketing|other (auto-reject). NULL on legacy rows + items that
  -- didn't enter via the queue. Enum enforced in score.py, not the DB.
  content_kind     TEXT,
  UNIQUE (consideration_id, slug)
);
CREATE INDEX IF NOT EXISTS idx_subs_cons ON sub_considerations(consideration_id);

CREATE TABLE IF NOT EXISTS sub_consideration_phases (
  sub_consideration_id INTEGER NOT NULL REFERENCES sub_considerations(id) ON DELETE CASCADE,
  phase_slug           TEXT    NOT NULL REFERENCES phases(slug),
  position             INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (sub_consideration_id, phase_slug)
);
CREATE INDEX IF NOT EXISTS idx_scp_phase ON sub_consideration_phases(phase_slug);

-- A sub-consideration can be placed under multiple considerations on
-- different page-types / components. Each row = one cons-umbrella the
-- sub lives under. Which page-types/components surface the sub is still
-- derived through consideration_destinations on each cons.
-- sub_considerations.consideration_id stays as the "primary placement"
-- (mirrored from position=0) so FTS joins and pending-row routing don't
-- have to change.
CREATE TABLE IF NOT EXISTS sub_consideration_placements (
  sub_id            INTEGER NOT NULL REFERENCES sub_considerations(id) ON DELETE CASCADE,
  consideration_id  INTEGER NOT NULL REFERENCES considerations(id)     ON DELETE CASCADE,
  position          INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (sub_id, consideration_id)
);
CREATE INDEX IF NOT EXISTS idx_sub_placements_cons ON sub_consideration_placements(consideration_id);
CREATE INDEX IF NOT EXISTS idx_sub_placements_sub  ON sub_consideration_placements(sub_id);

-- Page-type categories — virtual umbrellas that group several page_types.
-- A consideration can be attached to a category (via consideration_destinations
-- with dest_kind='category'); the read view expands the membership at query
-- time so the consideration surfaces on every page_type in the category.
CREATE TABLE IF NOT EXISTS page_type_categories (
  slug          TEXT PRIMARY KEY,
  label         TEXT NOT NULL,
  definition    TEXT NOT NULL DEFAULT '',
  display_order INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS page_type_in_category (
  category_slug   TEXT NOT NULL REFERENCES page_type_categories(slug),
  page_type_slug  TEXT NOT NULL REFERENCES page_types(slug),
  PRIMARY KEY (category_slug, page_type_slug)
);
CREATE INDEX IF NOT EXISTS idx_pt_in_cat_by_page ON page_type_in_category(page_type_slug);

-- A consideration can have many destinations. dest_kind is one of
-- 'page_type' | 'component' | 'category'. Replaces the single-parent
-- (parent_type, parent_slug) pair on considerations; those columns stay
-- during the migration window for backward compatibility but the join
-- table is the authoritative source going forward.
CREATE TABLE IF NOT EXISTS consideration_destinations (
  consideration_id INTEGER NOT NULL REFERENCES considerations(id) ON DELETE CASCADE,
  dest_kind        TEXT NOT NULL CHECK (dest_kind IN ('page_type','component','category')),
  dest_slug        TEXT NOT NULL,
  PRIMARY KEY (consideration_id, dest_kind, dest_slug)
);
CREATE INDEX IF NOT EXISTS idx_cons_dest_lookup ON consideration_destinations(dest_kind, dest_slug);

CREATE TABLE IF NOT EXISTS sources (
  id             INTEGER PRIMARY KEY,
  name           TEXT NOT NULL,
  type           TEXT NOT NULL CHECK (type IN ('rss','structured')),
  url            TEXT NOT NULL,
  status         TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','paused','error')),
  last_collected TEXT,
  item_count     INTEGER NOT NULL DEFAULT 0,
  config_json    TEXT NOT NULL DEFAULT '{}',
  created_at     TEXT NOT NULL,
  -- RFC 7232 conditional-GET caching for collect.py. NULL until first fetch.
  etag           TEXT,
  last_modified  TEXT,
  last_fetched   TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_sources_url ON sources(url);

-- Full-text search over approved sub_considerations + parent consideration
-- title/intro. rowid = sub_considerations.id. Populated by init_db.py
-- (rebuilt on every run) and, later, by admin write paths.
CREATE VIRTUAL TABLE IF NOT EXISTS subs_fts USING fts5(
  one_liner,
  body,
  cons_title,
  cons_intro,
  tokenize = 'unicode61 remove_diacritics 2'
);
