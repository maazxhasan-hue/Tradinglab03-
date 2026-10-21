# Nexora referral program, backups and recovery

## Referral model
- Clients receive a unique referral code after account registration.
- A valid code on the sign-up URL is attributed once to the new account; a referred account cannot be attributed twice.
- Referrals cover trading courses, websites, landing pages, AI tools/automation, and custom AI projects.
- Commission records use INR paise (integer) and a unique source reference to prevent duplicate commissions.
- An owner may record a commission only after explicitly confirming payment was received. The API stores an audit event. Do not treat a lead, enquiry, proposal, or trading outcome as a paid sale.
- No public rate or payout promise is made by default. Publish written commission terms before recruiting partners or making payouts.

## Deploy the schema and Worker
The existing GitHub Actions workflow `.github/workflows/deploy-intake-api.yml` applies versioned Cloudflare D1 migrations and deploys `worker/index.js` when Cloudflare deployment secrets are configured. Migration `0003_referral_program.sql` is additive; it preserves existing accounts and enquiries.
After deployment, test:
1. Register a test account with `?mode=signup&ref=VALIDCODE`.
2. Confirm the referral owner sees the sign-up in `GET /api/referrals/me`.
3. Confirm duplicate sign-up attribution is blocked by the unique referred-account constraint.
4. Record a synthetic commission only in a non-production test, and verify duplicate source references are rejected.
5. Confirm missing/invalid auth returns 401 and never exposes another user's referral data.

## Daily encrypted full D1 backup
Workflow: `.github/workflows/daily-d1-backup.yml`, scheduled daily at 01:23 UTC (06:53 IST). It exports the entire remote D1 database, encrypts it with AES-256-CBC using OpenSSL PBKDF2, verifies decryption matches the original, removes the plaintext export, and stores only the encrypted file plus SHA-256 checksum as a GitHub Actions artifact for 30 days.

Required GitHub Actions repository secrets:
- `CLOUDFLARE_API_TOKEN` — scoped to the account and D1 read/export permissions.
- `CLOUDFLARE_ACCOUNT_ID`.
- `BACKUP_ENCRYPTION_PASSPHRASE` — a long random passphrase kept offline in a password manager; never commit or share it.

**Until those secrets exist and a manual workflow run succeeds, daily backups are not operational.** A failed backup must be treated as an incident, not ignored. Review the Actions run and confirm it uploaded an encrypted artifact. The repository does not contain the passphrase.

## Restore and rollback
1. Download the encrypted artifact from a successful backup run and verify its checksum.
2. Decrypt it only on a trusted machine using the passphrase:
   `openssl enc -d -aes-256-cbc -pbkdf2 -in backup.sql.enc -out restore.sql -pass env:BACKUP_ENCRYPTION_PASSPHRASE`.
3. Restore into a separate/new D1 database first and validate schema, row counts, accounts, submissions, referrals, and commission records. Never test restoration against the only production database.
4. For an incident, pause writes and have an authorized operator approve the target and recovery point before restoring. A restore can overwrite newer records and cannot be automatically rolled back.
5. Keep the last known-good encrypted backup and retain a second offsite copy for long-term recovery.

## Migration rollback policy
Cloudflare D1 migrations are forward-only in this project. Do not drop referral tables or delete attribution records as a routine rollback. If the new feature needs disabling, disable the referral UI/API while leaving the additive schema intact. For data/schema recovery, restore a verified backup into a separate database and switch over only after validation and explicit operator approval.
