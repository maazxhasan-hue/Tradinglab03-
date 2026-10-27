CREATE TABLE IF NOT EXISTS leads (
  id TEXT PRIMARY KEY,
  dedupe_key TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  email TEXT NOT NULL DEFAULT '',
  phone TEXT NOT NULL DEFAULT '',
  interest TEXT NOT NULL DEFAULT '',
  source TEXT NOT NULL DEFAULT 'website',
  contact_consent INTEGER NOT NULL DEFAULT 0 CHECK (contact_consent IN (0,1)),
  contact_allowed INTEGER NOT NULL DEFAULT 0 CHECK (contact_allowed IN (0,1)),
  status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new','qualified','contacted','showing_scheduled','closed','lost')),
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ughq_leads_created_at ON leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ughq_leads_status ON leads(status);