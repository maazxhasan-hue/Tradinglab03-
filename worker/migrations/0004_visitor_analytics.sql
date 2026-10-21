-- Nexora visitor analytics: aggregate GA4 snapshots only; no raw events or personal identifiers.
CREATE TABLE IF NOT EXISTS visitor_daily_totals (
  site_id TEXT NOT NULL,
  snapshot_date TEXT NOT NULL,
  provider TEXT NOT NULL DEFAULT 'ga4'
    CHECK (provider IN ('ga4', 'edge_logs')),
  total_users INTEGER,
  sessions INTEGER NOT NULL DEFAULT 0,
  page_views INTEGER NOT NULL DEFAULT 0,
  engaged_sessions INTEGER,
  engagement_rate REAL,
  key_events REAL NOT NULL DEFAULT 0,
  data_status TEXT NOT NULL DEFAULT 'complete'
    CHECK (data_status IN ('complete', 'partial')),
  fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (site_id, snapshot_date, provider)
);

CREATE TABLE IF NOT EXISTS visitor_daily_sources (
  site_id TEXT NOT NULL,
  snapshot_date TEXT NOT NULL,
  provider TEXT NOT NULL DEFAULT 'ga4'
    CHECK (provider IN ('ga4', 'edge_logs')),
  source TEXT NOT NULL,
  medium TEXT NOT NULL,
  source_category TEXT NOT NULL DEFAULT 'other',
  sessions INTEGER NOT NULL DEFAULT 0,
  users INTEGER,
  page_views INTEGER NOT NULL DEFAULT 0,
  engaged_sessions INTEGER,
  engagement_rate REAL,
  key_events REAL NOT NULL DEFAULT 0,
  fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (site_id, snapshot_date, provider, source, medium)
);

CREATE TABLE IF NOT EXISTS visitor_daily_landing_pages (
  site_id TEXT NOT NULL,
  snapshot_date TEXT NOT NULL,
  provider TEXT NOT NULL DEFAULT 'ga4'
    CHECK (provider IN ('ga4', 'edge_logs')),
  landing_path TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT '(not set)',
  medium TEXT NOT NULL DEFAULT '(not set)',
  source_category TEXT NOT NULL DEFAULT 'other',
  sessions INTEGER NOT NULL DEFAULT 0,
  users INTEGER,
  key_events REAL NOT NULL DEFAULT 0,
  fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (site_id, snapshot_date, provider, landing_path, source, medium)
);

-- Range rows contain GA4 range-level metrics. Unique users are never derived by summing daily unique-user counts.
CREATE TABLE IF NOT EXISTS visitor_range_snapshots (
  site_id TEXT NOT NULL,
  snapshot_date TEXT NOT NULL,
  range_days INTEGER NOT NULL CHECK (range_days IN (7, 30, 90)),
  provider TEXT NOT NULL DEFAULT 'ga4' CHECK (provider = 'ga4'),
  total_users INTEGER,
  sessions INTEGER NOT NULL DEFAULT 0,
  page_views INTEGER NOT NULL DEFAULT 0,
  engaged_sessions INTEGER,
  engagement_rate REAL,
  key_events REAL NOT NULL DEFAULT 0,
  fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (site_id, snapshot_date, range_days, provider)
);

CREATE TABLE IF NOT EXISTS visitor_range_ai_metrics (
  site_id TEXT NOT NULL,
  snapshot_date TEXT NOT NULL,
  range_days INTEGER NOT NULL CHECK (range_days IN (7, 30, 90)),
  provider TEXT NOT NULL DEFAULT 'ga4' CHECK (provider = 'ga4'),
  total_users INTEGER,
  sessions INTEGER NOT NULL DEFAULT 0,
  page_views INTEGER NOT NULL DEFAULT 0,
  engaged_sessions INTEGER,
  engagement_rate REAL,
  key_events REAL NOT NULL DEFAULT 0,
  fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (site_id, snapshot_date, range_days, provider)
);

CREATE TABLE IF NOT EXISTS visitor_range_sources (
  site_id TEXT NOT NULL,
  snapshot_date TEXT NOT NULL,
  range_days INTEGER NOT NULL CHECK (range_days IN (7, 30, 90)),
  provider TEXT NOT NULL DEFAULT 'ga4' CHECK (provider = 'ga4'),
  source TEXT NOT NULL,
  medium TEXT NOT NULL,
  source_category TEXT NOT NULL DEFAULT 'other',
  sessions INTEGER NOT NULL DEFAULT 0,
  users INTEGER,
  page_views INTEGER NOT NULL DEFAULT 0,
  engaged_sessions INTEGER,
  engagement_rate REAL,
  key_events REAL NOT NULL DEFAULT 0,
  fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (site_id, snapshot_date, range_days, provider, source, medium)
);

CREATE TABLE IF NOT EXISTS visitor_range_landing_pages (
  site_id TEXT NOT NULL,
  snapshot_date TEXT NOT NULL,
  range_days INTEGER NOT NULL CHECK (range_days IN (7, 30, 90)),
  provider TEXT NOT NULL DEFAULT 'ga4' CHECK (provider = 'ga4'),
  landing_path TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT '(not set)',
  medium TEXT NOT NULL DEFAULT '(not set)',
  source_category TEXT NOT NULL DEFAULT 'other',
  sessions INTEGER NOT NULL DEFAULT 0,
  users INTEGER,
  key_events REAL NOT NULL DEFAULT 0,
  fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (site_id, snapshot_date, range_days, provider, landing_path, source, medium)
);

CREATE TABLE IF NOT EXISTS ai_referral_domains (
  hostname TEXT PRIMARY KEY,
  platform_name TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO ai_referral_domains (hostname, platform_name) VALUES
  ('chatgpt.com', 'ChatGPT'),
  ('chat.openai.com', 'ChatGPT'),
  ('perplexity.ai', 'Perplexity'),
  ('claude.ai', 'Claude'),
  ('gemini.google.com', 'Gemini'),
  ('copilot.microsoft.com', 'Copilot'),
  ('copilot.com', 'Copilot'),
  ('poe.com', 'Poe'),
  ('you.com', 'You.com'),
  ('phind.com', 'Phind'),
  ('meta.ai', 'Meta AI'),
  ('deepseek.com', 'DeepSeek'),
  ('mistral.ai', 'Mistral'),
  ('huggingface.co', 'HuggingChat');

CREATE TABLE IF NOT EXISTS visitor_sync_runs (
  id TEXT PRIMARY KEY,
  provider TEXT NOT NULL DEFAULT 'ga4',
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL CHECK (status IN ('running', 'success', 'partial', 'failed', 'not_configured')),
  rows_processed INTEGER NOT NULL DEFAULT 0,
  snapshot_date TEXT,
  error_code TEXT,
  error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_visitor_daily_totals_date
  ON visitor_daily_totals(site_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_visitor_daily_sources_date_category
  ON visitor_daily_sources(site_id, snapshot_date DESC, source_category);
CREATE INDEX IF NOT EXISTS idx_visitor_daily_landing_date
  ON visitor_daily_landing_pages(site_id, snapshot_date DESC, landing_path);
CREATE INDEX IF NOT EXISTS idx_visitor_range_sources
  ON visitor_range_sources(site_id, range_days, snapshot_date DESC, source_category);
CREATE INDEX IF NOT EXISTS idx_visitor_range_landing
  ON visitor_range_landing_pages(site_id, range_days, snapshot_date DESC, sessions DESC);
CREATE INDEX IF NOT EXISTS idx_visitor_sync_runs_status
  ON visitor_sync_runs(provider, status, started_at DESC);
