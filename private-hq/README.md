# Private HQ — Visitor Analytics

This folder contains the protected Nexora company HQ and its visitor analytics feature. **The analytics screen is an owner-only report, not a public dashboard.** The worker API independently requires the owner API key for every analytics read or manual sync.

## Files in this folder

- `index.html` — main private HQ, including the compact Website Visitor Tracker widget.
- `visitor-analytics.html` — full-page report with 7/30/90-day filters, trend, metrics, source attribution, AI-source breakdown, landing pages, and sync health.
- `visitor-analytics-ui.js` — shared UI logic for the compact widget and full report. It sends the owner key in an HTTPS Authorization header only; it never stores the key in browser storage.
- `agent-town.html`, `harvey.html`, `inbox.html`, `marketing.html` — other protected HQ pages.

The root `private_hq_server.py` authenticates all listed pages and their assets with an HttpOnly, Secure, SameSite=Strict session cookie. It must serve JavaScript as `text/javascript`; the analytics file allowlist and MIME handling are covered by `tests/test_private_hq_static_assets.py`. `Dockerfile.private-hq` copies the full `private-hq/` folder into the server image.

## Data flow

1. The public site loads `dashboard/analytics-consent.js`. The script requests only the public Measurement ID from `GET /api/analytics/config`; it sends no Google Analytics request until analytics consent is granted. It honours browser Global Privacy Control and Do Not Track signals.
2. The Cloudflare Worker fetches reports from the GA4 Data API using server-side service-account credentials.
3. The Worker aggregates daily totals, traffic-source breakdowns, and landing-page rows into Cloudflare D1. It stores aggregate reporting data only, not raw event streams or personal identifiers.
4. The private HQ calls `GET /api/admin/analytics/visitors?days=7|30|90` to read the snapshots. A manual refresh calls `POST /api/admin/analytics/sync`.
5. The Worker cron trigger refreshes the last 90 days of reports daily. Re-runs use upserts so they refresh rows rather than multiplying counts.

The configured AI-referral domains are seeded by `worker/migrations/0004_visitor_analytics.sql`. Unknown and unidentifiable sources stay separate; an AI referral is not the same thing as an automated AI crawler request.

## Required configuration

Set these **GitHub Actions repository variables**:

- `NEXORA_GA4_PROPERTY_ID` — numeric GA4 property ID, not the Measurement ID.
- `NEXORA_GA4_MEASUREMENT_ID` — verified web stream ID such as `G-XXXXXXXXXX`.

Set these **GitHub Actions repository secrets**:

- `NEXORA_GA4_CLIENT_EMAIL` — Google service-account email.
- `NEXORA_GA4_PRIVATE_KEY` — the service-account private key in PEM format. Keep it only as a secret; do not commit it.
- `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` — the deployment workflow's existing Cloudflare credentials.
- `TRADINGLAB03_ADMIN_API_KEY` — the owner key used for protected Worker admin endpoints.

In Google Cloud, enable the Google Analytics Data API and grant the service account **Viewer** access to the intended GA4 property. Use the same GA4 property and Measurement ID for the public site. The allowed public website origin and the private HQ origin must both appear in the Worker deployment's origin allowlist. Do not configure an unrelated host just to bypass a CORS error.

The deployment workflow writes the credential secrets into Worker secrets and Measurement ID/property ID as Worker variables. It does not print secret values. Once the GA4 variables/secrets are missing, the dashboard must show **Not connected**; it must not replace missing values with example counts.

## Local validation and safe rollout

Run:

```bash
python -m unittest discover -s tests -v
node --check worker/index.js
node --check private-hq/visitor-analytics-ui.js
node --check dashboard/analytics-consent.js
```

Before production use, confirm the service-account permission, grant consent on the real public site, check that reports appear in GA4, manually sync from the owner-only report, compare totals against GA4 for the same dates, confirm the `generate_lead` event fires only after an enquiry is saved, and test the 401/403 cases. Do not send sample enquiries or create fake traffic merely to populate the dashboard.

The source code and deployment configuration alone do not prove that production credentials, daily backups, the Render service, or live GA4 ingestion are configured. Verify each through its deployment/run history and a successful live smoke test before calling the feature production-ready.
