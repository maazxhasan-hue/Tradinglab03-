-- Nexora referral program (Cloudflare D1 / SQLite).
-- Additive only: existing accounts and enquiries are preserved.
ALTER TABLE client_accounts ADD COLUMN referral_code TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_client_accounts_referral_code
  ON client_accounts(referral_code) WHERE referral_code IS NOT NULL;

CREATE TABLE IF NOT EXISTS referrals (
  id TEXT PRIMARY KEY,
  referrer_account_id TEXT NOT NULL REFERENCES client_accounts(id) ON DELETE RESTRICT,
  referred_account_id TEXT NOT NULL UNIQUE REFERENCES client_accounts(id) ON DELETE RESTRICT,
  referral_code TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'registered'
    CHECK (status IN ('registered','qualified','converted','rejected')),
  created_at TEXT NOT NULL,
  qualified_at TEXT,
  converted_at TEXT,
  notes TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_created
  ON referrals(referrer_account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_referrals_status_created
  ON referrals(status, created_at DESC);

-- Commission ledger stores integer paise, never floating-point currency.
-- A commission is only payable after an owner verifies received client payment.
CREATE TABLE IF NOT EXISTS referral_commissions (
  id TEXT PRIMARY KEY,
  referral_id TEXT NOT NULL REFERENCES referrals(id) ON DELETE RESTRICT,
  source_type TEXT NOT NULL CHECK (source_type IN ('trading_course','website','landing_page','ai_tool','custom_project','other')),
  source_reference TEXT NOT NULL,
  gross_amount_paise INTEGER NOT NULL CHECK (gross_amount_paise >= 0),
  commission_rate_bps INTEGER NOT NULL CHECK (commission_rate_bps BETWEEN 0 AND 10000),
  commission_amount_paise INTEGER NOT NULL CHECK (commission_amount_paise >= 0),
  currency TEXT NOT NULL DEFAULT 'INR' CHECK (currency = 'INR'),
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending','approved','paid','reversed')),
  payment_verified_at TEXT,
  approved_at TEXT,
  paid_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(source_type, source_reference)
);
CREATE INDEX IF NOT EXISTS idx_referral_commissions_referral_status
  ON referral_commissions(referral_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS referral_audit_log (
  id TEXT PRIMARY KEY,
  actor_type TEXT NOT NULL CHECK (actor_type IN ('system','owner')),
  actor_id TEXT NOT NULL DEFAULT '',
  event_type TEXT NOT NULL,
  referral_id TEXT,
  commission_id TEXT,
  details_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_referral_audit_created
  ON referral_audit_log(created_at DESC);
