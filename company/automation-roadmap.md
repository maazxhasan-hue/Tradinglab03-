# Company Automation Roadmap

Last reviewed: 2026-10-15

## Current confirmed baseline

- Hourly opportunity scout workflow exists: `.github/workflows/hourly-opportunity-scout.yml`; Freelancer.com sources and API setup have been disabled by owner choice, and the workflow now scans only enabled public sources.
- Manual AI draft worker exists: `.github/workflows/agent-worker.yml`. Its current template mode is not proof of a connected LLM provider.
- Scheduled company health check exists: `.github/workflows/company-health-check.yml`.
- Operating controls require separate human authorization for sensitive actions.
- Proposal preparation and opportunity review documents exist under `data/opportunities/`.

## What this does not mean

The repository alone does not establish that the website is continuously reachable, scheduled workflows are enabled and completing, a cloud service is running, any client has hired the company, or revenue is being earned. Scheduled GitHub Actions are periodic jobs, not a permanently running worker.

## Phased implementation plan

### Phase 1 — Reliable discovery and reporting
- Do not use Freelancer.com; its configured source entries are disabled and the scout no longer installs its SDK or reads its token.
- Keep the public RSS sources already enabled (Reddit r/forhire and Codeur); do not assume they provide enough volume or all sources are accessible on every run.
- Keep the hourly scout on a schedule and allow manual runs.
- Store timestamped reports and deduplicate leads.
- Make test failures fail the workflow and upload logs even on failure.
- Verify actual scheduled runs and review artifacts before calling the system healthy.

### Phase 2 — Proposal drafting
- Use a configured AI provider only when a secret is deliberately added by the repository owner.
- Draft proposals against verified project requirements; do not invent experience, credentials, or portfolio claims.
- Save drafts for review. Do not auto-submit proposals, send direct messages, or accept terms.

### Phase 3 — Delivery workflow
- Add a project board with stages: lead, qualified, draft ready, awaiting approval, submitted, client reply, contracted, in progress, QA, delivered, invoiced, paid, closed.
- Require a human to confirm contracts, scope, deadlines, and client commitments.
- Add reusable project checklists and QA reports.

### Phase 4 — Marketing and support
- Generate a content calendar and draft posts.
- Connect publishing and inbox integrations only after the owner authorizes the account and platform permissions.
- Keep public posting, customer messages, refunds, and paid promotion behind explicit approval until safeguards and monitoring are tested.

### Phase 5 — Finance and alerts
- Track invoices, due dates, expenses, and confirmed payments; never infer payment from a proposal or invoice being created.
- Alert on failed workflow runs, stale discovery data, overdue client replies, and unpaid invoices only after a notification channel is configured and tested.
- Do not purchase subscriptions or services automatically.

## Safety boundaries

- Do not change any trading bot, Angel One, or MCX configuration as part of company automation.
- Do not store credentials in source files or commit logs.
- Do not make financial commitments, submit bids, send client messages, sign agreements, or issue refunds without the required owner authorization.

## Acceptance criteria for claiming "mostly automated"

1. Recent scheduled runs are visible and successful.
2. Reports/artifacts are inspected and contain expected data.
3. The AI provider is explicitly configured and a test draft is reviewed.
4. Client/project status tracking is used end-to-end.
5. Notifications are tested on an actual authorized channel.
6. Any human approval gates are documented and working.
7. Failures generate actionable alerts; no workflow is described as 24/7 unless the actual service and monitoring prove it.
