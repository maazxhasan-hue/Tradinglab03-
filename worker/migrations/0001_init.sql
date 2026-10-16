CREATE TABLE IF NOT EXISTS submissions (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  company TEXT NOT NULL DEFAULT '',
  service TEXT NOT NULL,
  budget TEXT NOT NULL DEFAULT '',
  deadline TEXT NOT NULL DEFAULT '',
  goal TEXT NOT NULL,
  reference_url TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'new',
  ip_hash TEXT NOT NULL,
  notification_status TEXT NOT NULL DEFAULT 'not_configured'
);
CREATE INDEX IF NOT EXISTS idx_submissions_created_at ON submissions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_ip_created ON submissions(ip_hash, created_at);
CREATE INDEX IF NOT EXISTS idx_submissions_status_created ON submissions(status, created_at DESC);
