CREATE TABLE IF NOT EXISTS client_rate_limit_events (
  id TEXT PRIMARY KEY,
  bucket_hash TEXT NOT NULL,
  route_type TEXT NOT NULL,
  outcome TEXT NOT NULL DEFAULT 'attempt',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rate_limit_bucket_time ON client_rate_limit_events(bucket_hash, route_type, created_at);
