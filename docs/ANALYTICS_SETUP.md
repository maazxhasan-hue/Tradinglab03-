# Nexora AI visitor analytics — setup and verification

## Implementation status

The repository contains:
- A consent-gated GA4 loader for the public Nexora website (`dashboard/analytics-consent.js`). It does not load Google Analytics until the visitor explicitly allows analytics, and it respects browser Global Privacy Control and Do Not Track.
- A Worker endpoint at `GET /api/analytics/config` that exposes only the public Measurement ID when configured.
- A scheduled GA4 ingestion job in `worker/index.js`, with aggregated snapshots in Cloudflare D1 and a manually triggered owner-only sync endpoint.
- A private HQ widget and full report at `private-hq/index.html`, `private-hq/visitor-analytics.html`, and `private-hq/visitor-analytics-ui.js`.
- Daily totals, source breakdowns, landing pages, range totals, AI-referral classifications, and sync status. The report deliberately shows dashes when no successful data is available.

The code is not considered production-verified until the GA4 property and credentials below are configured, a live sync succeeds, and the private HQ is served from an authenticated/private host. The public GitHub Pages allowlist intentionally does not publish `private-hq/`.

## Configure Google Analytics 4

1. Sign in to [Google Analytics](https://analytics.google.com/) with the business Google account.
2. Create or identify the Nexora AI GA4 property and add a Web data stream for the actual production website hostname.
3. Copy the stream Measurement ID (format `G-XXXXXXXXXX`) and the numeric GA4 property ID.
4. In the GitHub repository settings, add these **Actions variables**:
   - `NEXORA_GA4_PROPERTY_ID` — numeric GA4 property ID.
   - `NEXORA_GA4_MEASUREMENT_ID` — verified Web stream Measurement ID, beginning with `G-`.
5. Create a Google Cloud service account and enable the Google Analytics Data API for its project. Grant the service-account email **Viewer** access to the correct GA4 property.
6. Add these **GitHub Actions secrets**:
   - `NEXORA_GA4_CLIENT_EMAIL` — service-account email.
   - `NEXORA_GA4_PRIVATE_KEY` — the service account's PEM private key. Store the complete key securely; never commit it, paste it into website code, or print it in logs.
7. Trigger the `Deploy TradingLab03 Intake API` workflow (or push an approved Worker change). It reads the variables, configures the Worker Measurement ID, and uploads the service-account credentials as Worker secrets without printing their values.
8. Trigger the website deployment workflow so the public pages include the latest consent-gated loader. The loader reads the public Measurement ID from the Worker; no GA request should be sent before consent is granted.

## Run and verify the first sync

1. Open the private HQ on its authenticated/private hosting target and open **Website visitor tracker**.
2. Paste the Worker owner key into the key field. The page keeps it in memory only; it does not save it to local storage.
3. Select **Sync GA4 now** and wait for a successful result. If the service account lacks property access or any credentials are wrong, the dashboard should show an actionable failure rather than fabricated counts.
4. Load the report and compare totals with the equivalent GA4 reports for the same period and property.
5. Visit the public website in a fresh browser session, select **Allow analytics**, and confirm real-time activity in GA4. Select **Only necessary** in a separate session and confirm the Google tag is not loaded.
6. Verify the source breakdown, AI-referral classification, landing-page table, and key events using actual test traffic. Do not generate fake business conversion events.
7. Confirm that a repeat sync updates existing rows rather than duplicating them, and that a failed sync leaves the last good snapshot visible with the sync failure clearly labelled.

## Report semantics and limitations

- The GA4 total-users metric is fetched separately for the entire selected range. Never calculate period-wide unique users by summing daily or source-level users; those values can overlap.
- AI referrals are identifiable human sessions classified from GA4 source/medium and the configured AI domain list. They are not proof that an AI model recommended Nexora.
- Edge/server request logs, if added later, must be reported separately from GA4 sessions and users. Do not add these metrics together.
- A missing Measurement ID, missing credentials, or lack of a successful sync is shown as not configured / no data, never as zero visitors.
- Historical data is limited to what GA4 reports for the selected property and what has been ingested. Late-arriving data can change recent reports, so the scheduled sync re-fetches the recent reporting window.
- The private HQ must not be deployed to a public static host without access control. Keep owner API keys server-side where possible; the current manual key entry is sent only to the configured HTTPS Worker API and is not persisted by the page.

## Privacy and launch checks

- Do not track before consent where required. Respect the site's privacy notice and provide a way to change consent.
- Respect Global Privacy Control and Do Not Track signals as implemented in the loader.
- Never send names, email addresses, phone numbers, UPI IDs, payment references, or project form contents to GA4.
- Landing paths are stored without query strings and are scrubbed for obvious email-address patterns.
- Keep Google credentials in GitHub Actions secrets and Cloudflare Worker secrets only.
- Verify the privacy notice and applicable consent requirements before enabling analytics for production visitors.
- After the production hostname is finalized, verify the canonical sitemap and Search Console property separately.
