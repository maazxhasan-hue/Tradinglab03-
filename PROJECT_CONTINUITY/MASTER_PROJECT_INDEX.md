# Nexora AI / TradingLab03 — Master Project Index
Updated: 2026-10-21

This is the central index for the existing project. The repository remains the source of truth for source code and deployment configuration. This document organizes the work; it does not imply that external services, plugins, or secrets are installed/configured.

## Main project
- Repository: https://github.com/maazxhasan-hue/Tradinglab03-
- Public website: https://nexora-ai-public.netlify.app/
- Intended business: trading education/courses, business websites, landing pages, AI tools/chatbots, automation, and custom AI builds.
- Main app source: `dashboard/`
- Worker/API and database migrations: `worker/`
- Owner/admin UI: `private-hq/`
- Long-lived project notes: `PROJECT_CONTINUITY/`

## Current implementation areas
- Public website and client project enquiry flow: `dashboard/website.html`
- Client sign-in/sign-up: `dashboard/login.html`
- Client referral dashboard: `dashboard/referrals.html`
- Referral program schema: `worker/migrations/0003_referral_program.sql`
- Referral and owner commission endpoints: `worker/index.js`
- Daily encrypted D1 backup workflow: `.github/workflows/daily-d1-backup.yml`
- Recovery and rollback instructions: `docs/REFERRALS_BACKUPS_AND_RECOVERY.md`
- Intake API deployment workflow: `.github/workflows/deploy-intake-api.yml`
- Visitor analytics schema: `worker/migrations/0004_visitor_analytics.sql`
- Shared Brain implementation/architecture: see the dated Shared Brain files in this folder.
- Private HQ source pages: `private-hq/`; deployment must remain access-controlled and must not expose private owner data.

## Important verification status
- The latest public website deployment workflow reported success for commit `57cc744dbf0902751cdcf29b22d4ba8ed1d8dd91` on 2026-10-21.
- That result is for the website workflow only. It does **not** prove the referral Worker/migration deployed or that the D1 backup workflow succeeded.
- Referral Worker deployment, D1 migration status, referral sign-up smoke tests, owner commission tests, backup secrets, encrypted artifact upload, and restore drill must each be checked independently.
- Required backup secret *names*: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `BACKUP_ENCRYPTION_PASSPHRASE`. Never write their values in the repository.
- The deployment workflow uses `TRADINGLAB03_ADMIN_API_KEY`; verify that it exists in GitHub Actions secrets before relying on owner endpoints.
- The backup workflow keeps encrypted artifacts for 30 days. A restore must first be tested into a separate database; never test over production.

## Codex / 21st.dev / Figma requests
- Requested Codex plugin marketplace source: https://github.com/21st-dev/codex-plugin
- Requested design tooling: Figma integration / frame link.
- These are recorded as requested integrations, not as installed in ChatGPT. Adding a repository link or configuration file does not install a plugin in the ChatGPT mobile app. Any Codex plugin setup must follow the current supported Codex/ChatGPT product workflow and the plugin's own installation instructions.
- Keep design files and exported assets in the project's relevant design/assets folder once created. Do not invent a Figma file/frame URL; add the real URL when it is available.

## Release and safety rules
1. Read `PROJECT_CONTINUITY/STATE.md` before editing.
2. Preserve existing functionality; use small, reviewable changes.
3. Run syntax checks, migration-chain tests, unit tests, and relevant workflow checks before calling a change complete.
4. Verify the actual deployed URL/API after deployment; a commit alone is not deployment proof.
5. Never store secrets, customer data, account credentials, or private trading keys in Git.
6. Do not promise trading profits or guaranteed referral commissions. Commission records must represent verified customer payments.
7. Treat D1 migrations as forward-only. Disable a feature rather than destructively dropping data; restore backups to a separate database first.
8. After meaningful work, update `STATE.md`, append to `CHANGELOG.md`, and log verification plus the next exact step.

## Next actions
1. Verify the intake API deployment workflow and D1 migration chain.
2. Confirm referral endpoints and signup attribution on a test account.
3. Add and verify backup secrets, manually run the backup workflow, and confirm the encrypted artifact/checksum exists.
4. Perform a non-production restore drill and document results.
5. Complete supported Codex plugin and Figma setup after confirming the exact product environment and real Figma frame URL.
6. Only after functional fixes and release checks, apply the requested private HQ theme.
