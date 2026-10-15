# Opportunity source policy

## Goal
Find actionable public project requests for digital services while keeping the hourly scout reliable, free-first, and compliant. A listing is a lead to review, never proof of a real buyer, payment, or contract.

## Current source posture
- **Codeur public RSS** — enabled; mostly French-language project requests. Manually check language, eligibility, budget, scope, deadline, platform costs, and whether the listing is still open.
- **Reddit r/forhire RSS** — enabled; public posts are unverified and subreddit rules apply. Never automate posts, comments, or DMs.
- **Freelancer.com** — disabled by owner decision on 2026-10-15. Its sources are disabled in config, and its SDK/token setup was removed from the scout workflow. Do not re-enable unless the owner explicitly changes this decision.
- **Reddit r/DesignJobs and r/hiring** — disabled after HTTP 429 throttling. Do not poll repeatedly or rotate identities to bypass limits.
- **XPlace feeds** — disabled after HTTP 404; do not re-enable until a valid feed is independently confirmed.
- **General remote-job feeds** — disabled in the direct-client scan because employee vacancies dilute buyer-intent results.
- **Other feeds** — keep disabled when a live runner has received access challenges, errors, or unstable responses.

## Adding a source
1. Prefer an official public RSS/Atom feed or an officially documented API.
2. Verify the endpoint, response format, update frequency, rate limits, attribution requirements, and usage terms before enabling it.
3. Keep requests low-volume, add a timeout, deduplicate by canonical listing URL, and record source-specific failures.
4. Keep direct buyer projects separate from job vacancies and freelance-role opportunities.
5. Preserve the original listing URL and source name. Do not scrape login-only pages or bypass access controls, CAPTCHAs, or rate limits.
6. Keep `paid_contract_verified` false until a human independently verifies payment terms and legitimacy.
7. Never auto-message, bid, apply, purchase a subscription, or claim revenue from discovery alone.

## Next free-first channels
- Keep the two enabled public feeds and inspect real run artifacts for useful buyer-intent results.
- Improve the portfolio sample and website contact path using verified owner contact details; placeholders must remain clearly marked until replaced.
- Prepare targeted content and manual prospect research as drafts; do not publish or contact people without approval.
- Do not add a source just because it is free. Test its accessibility and lead quality first.

## Current limitations
The current enabled feeds do not guarantee sufficient lead volume, verified clients, or income. The repository has no authenticated inbox/social account connection for outbound outreach. Scheduled GitHub Actions are periodic jobs, not proof of a continuously running 24/7 agent. No paid subscriptions or API services should be added without explicit approval.
