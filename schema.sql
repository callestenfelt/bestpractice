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
  display_order   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS components (
  slug          TEXT PRIMARY KEY,
  label         TEXT NOT NULL,
  definition    TEXT NOT NULL DEFAULT '',
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

CREATE TABLE IF NOT EXISTS sources (
  id             INTEGER PRIMARY KEY,
  name           TEXT NOT NULL,
  type           TEXT NOT NULL CHECK (type IN ('rss','structured')),
  url            TEXT NOT NULL,
  status         TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','paused','error')),
  last_collected TEXT,
  item_count     INTEGER NOT NULL DEFAULT 0,
  config_json    TEXT NOT NULL DEFAULT '{}',
  created_at     TEXT NOT NULL
);

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
