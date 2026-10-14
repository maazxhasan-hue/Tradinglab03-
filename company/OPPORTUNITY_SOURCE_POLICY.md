# Opportunity source policy

## Goal
Find actionable public project requests for digital services while keeping the hourly scout reliable, low-cost, and compliant. A listing is a lead to review, never proof of a real buyer, payment, or contract.

## Current source posture
- **Codeur public RSS** — enabled; mostly French-language project requests. Manually check language, eligibility, budget, scope, deadline, and whether the listing is still open.
- **Reddit r/forhire RSS** — enabled; public posts are unverified and subreddit rules apply.
- **Reddit r/DesignJobs and r/hiring** — disabled after HTTP 429 throttling. Do not poll repeatedly or rotate identities to bypass limits.
- **XPlace feeds** — disabled after HTTP 404; do not re-enable until a valid feed is independently confirmed.
- **General remote-job feeds** — disabled in the direct-client scan because employee vacancies dilute buyer-intent results.

## Adding a source
1. Prefer an official public RSS/Atom feed or an officially documented API.
2. Verify the endpoint, response format, update frequency, rate limits, attribution requirements, and usage terms before enabling it.
3. Keep requests low-volume, add a timeout, deduplicate by canonical listing URL, and record source-specific failures.
4. Keep direct buyer projects separate from job vacancies and freelance-role opportunities.
5. Preserve the original listing URL and source name. Do not scrape login-only pages or bypass access controls, CAPTCHAs, or rate limits.
6. Keep paid_contract_verified false until a human independently verifies payment terms and legitimacy.
7. Never auto-message, bid, apply, purchase a subscription, or claim revenue from discovery alone.

## Freelancer.com API assessment
Freelancer.com now has a free, read-only fallback that makes one bounded GET request to the publicly accessible active-project endpoint (`/api/projects/0.1/projects/active/`) when no token is configured. When an authorized token is present, the collector can use the official Python SDK. This public endpoint has been reported to return active public projects without authentication, but its anonymous access and response schema are not guaranteed by the SDK docs and may change; the workflow tests parsing with fixtures, while live availability still needs to be confirmed by the next Actions run. Do not bypass authentication, CAPTCHAs, or rate limits. On HTTP errors the source is recorded as an error and other sources continue. Never commit tokens or place them in reports/artifacts. No paid proxy or subscription is used.

References:
- Official developer portal: https://developers.freelancer.com/
- Official Python SDK: https://github.com/freelancer/freelancer-sdk-python
- API terms: https://www.freelancer.com/about/apiterms


Freelancer.com integration update: an optional read-only adapter is committed. It skips cleanly when `FREELANCER_API_TOKEN` is absent and does not bid, message, apply, or spend money. Live API behavior remains unverified until an authorized secret is configured.
