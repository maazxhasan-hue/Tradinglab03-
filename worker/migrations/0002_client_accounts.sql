CREATE TABLE IF NOT EXISTS client_accounts (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  password_salt TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  disabled INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS client_sessions (
  token_hash TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  FOREIGN KEY (account_id) REFERENCES client_accounts(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_client_sessions_account ON client_sessions(account_id);
CREATE INDEX IF NOT EXISTS idx_client_sessions_expiry ON client_sessions(expires_at);
ALTER TABLE submissions ADD COLUMN account_id TEXT NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_submissions_account_created ON submissions(account_id, created_at DESC);
CREATE TABLE IF NOT EXISTS client_auth_attempts (
  id TEXT PRIMARY KEY,
  ip_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_client_auth_attempts_ip_created ON client_auth_attempts(ip_hash, created_at);
