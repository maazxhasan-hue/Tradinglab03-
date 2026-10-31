# 24/7 Operations — Current Implementation and Gaps

Updated 2026-10-15.

## What this repository actually provides

- The static HQ dashboard can be served by GitHub Pages; a live page is not proof that background agents are executing.
- The Opportunity Scout workflow is scheduled hourly at minute 17 UTC, supports manual dispatch, runs qualification tests, fetches public listings, imports eligible listings, and uploads a report artifact. It is a scheduled job, not an always-running process.
- The AI Draft Worker runs only when manually dispatched. Its current workflow explicitly sets `AI_PROVIDER=template`, so it must not be described as a connected autonomous AI model.
- Governance helpers block sensitive actions without explicit human approval. Do not bypass these controls to claim full autonomy.
- No evidence in this repository alone proves that all departments are staffed, that external client proposals are submitted, or that revenue is being generated.

## Added reliability check

`.github/workflows/company-health-monitor.yml` checks the full Python test suite and fetches the public HQ homepage twice an hour, offset from the top of the hour. It can detect certain failures, but GitHub Actions scheduling can be delayed or skipped. It is not a guarantee of 24/7 uptime, and it does not automatically repair a failed deployment or send an external alert.

## What still requires setup or human ownership

1. Enable notifications for failed GitHub Actions runs in repository/account settings.
2. Verify the latest successful runs in the Actions tab after the first monitor run.
3. Add a true always-on worker only for tasks that require continuous execution; use a managed process supervisor, health endpoint, restart policy, and logs. Do not put private trading/brokerage credentials into this business repo.
4. Add a connected AI provider secret only if desired; never paste secrets into source code or chat. Run drafts in approval mode.
5. Configure external alerting (email/Telegram/etc.) only after the account/connector and destination are authorized. No alert integration is configured by this commit.
6. Keep proposals, contracts, spending, publishing, customer-data access, deployments, and refunds behind human approval.
7. Establish service terms, privacy and retention policies, backups/restore tests, a client delivery checklist, invoicing/payment reconciliation, and an accountable human owner.

## Safe operational definition

“24/7” should mean: public status is checked on a schedule, failures generate actionable alerts, long-running workers have health checks and automatic restarts, tasks are durably queued/retried, and sensitive actions remain approval-gated. This repository is not yet at that level; the new monitor is one incremental reliability control.
