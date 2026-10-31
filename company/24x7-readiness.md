# 24/7 Readiness and Operating Status

Last reviewed: 2026-10-15

## What is actually automated now

- **Public opportunity discovery:** `.github/workflows/hourly-opportunity-scout.yml` is configured for hourly runs at minute 17 UTC, plus manual dispatch and selected pushes. It reads public feeds and imports qualifying listings. GitHub can delay or drop scheduled runs during high load, and public-repository schedules can be disabled after 60 days without repository activity. A configured cron is not proof that the workflow is enabled or every run succeeded.
- **Company health checks:** `.github/workflows/company-health-check.yml` is configured every 6 hours, on selected company/test changes, and manually. It runs the Python test suite, checks required files and source-config JSON, and uploads a report artifact. It checks repository code/configuration only.
- **AI draft worker:** `.github/workflows/agent-worker.yml` runs manually when triggered. It is not an always-on agent. The current workflow uses template mode; an API key or LLM provider connection is not implied.
- **Website/dashboard:** GitHub Pages can serve static files independently, but a visible dashboard is not proof that backend workers or agents are running continuously.
- **Governance:** bid submission, customer messaging, purchases, paid subscriptions, deployment to client sites, and other sensitive actions require explicit human approval. Do not remove these safeguards to claim autonomy.

## What this health check cannot prove

The repository workflow cannot verify account eligibility on freelance platforms, live cloud VM processes, live website uptime, secrets validity, billing limits, whether scheduled workflows are enabled in GitHub settings, or client income. These require separate live checks and authorized access. No proposals, messages, purchases, or account registrations are performed by this workflow.

## How to use it

1. Open [Company Health Check workflow](https://github.com/maazxhasan-hue/Tradinglab03-/actions/workflows/company-health-check.yml).
2. Use **Run workflow** to trigger the first check. The workflow is also scheduled every 6 hours once enabled on the default branch.
3. Open the run and download its `company-health-<run_id>` artifact for the report and test log.
4. Open [Hourly Opportunity Scout](https://github.com/maazxhasan-hue/Tradinglab03-/actions/workflows/hourly-opportunity-scout.yml) and verify recent scheduled runs show success. If there is no recent run, check whether the workflow is disabled and whether GitHub Actions is enabled for the repository.
5. Review failures; do not treat a green repository check as proof that external integrations or revenue workflows work.

## Definition of "24/7"

The company is not a fully autonomous 24/7 operation yet. It has scheduled automation and on-demand workers, but it still needs external service monitoring, authenticated integration checks, incident notifications, persistent worker health checks where needed, and human approval for commercial commitments. Never claim continuous operation or revenue unless logs and verified receipts support it.
