CREATE TABLE IF NOT EXISTS client_auth_attempts (
  id TEXT PRIMARY KEY,
  ip_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_client_auth_attempts_ip_created ON client_auth_attempts(ip_hash, created_at);
