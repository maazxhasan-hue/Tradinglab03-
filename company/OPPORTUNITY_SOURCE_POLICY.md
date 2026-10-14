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
Freelancer.com publishes an official developer API and an official Python SDK, but the SDK documentation requires an OAuth token. This is not a plug-and-play anonymous RSS feed. Do not enable a Freelancer.com integration until an authorized token is supplied through GitHub Actions secrets/environment variables, the exact read-only project-search endpoint and permitted use are confirmed against official documentation, and tests cover authentication failures, rate limits, and response parsing. Never commit tokens or place them in reports/artifacts. No paid third-party API proxy is approved by this policy.

References:
- Official developer portal: https://developers.freelancer.com/
- Official Python SDK: https://github.com/freelancer/freelancer-sdk-python
- API terms: https://www.freelancer.com/about/apiterms
