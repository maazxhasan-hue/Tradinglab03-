# Nexora AI — Delivery & Release Runbook
Updated: 17 October 2026

This repository contains the public services website, client login/intake flow, Cloudflare Worker API, owner inbox UI, internal workflow pages, marketing drafts, automation workflows, tests, and operational documentation.

## Live entry points
- Public website: https://nexora-ai-public.onrender.com
- Client project intake: https://nexora-ai-public.onrender.com/dashboard/website.html
- Client login: https://nexora-ai-public.onrender.com/dashboard/login.html
- Company HQ: https://nexora-internal-hq.onrender.com/
- Marketing Studio: public transition notice at https://nexora-internal-hq.onrender.com/marketing.html; full private studio is not currently deployed.
- Owner inbox UI: not yet privately hosted; use the owner-key-protected API from a trusted environment until server-enforced access is deployed.
- Source repository: https://github.com/maazxhasan-hue/Tradinglab03-
- CI workflows: https://github.com/maazxhasan-hue/Tradinglab03-/actions

## What exists in source
- Public marketing website and client project-intake form.
- Client registration/login API and token-protected intake submission.
- Cloudflare Worker + D1 intake API, owner-key-protected inbox API, spam/rate controls, and optional Resend notifications.
- Opportunity discovery, lead scoring, proposal and client-pack generation, bounded agent workflows, draft marketing calendar, and CI quality checks.
- Automated tests and workflow artifacts for reviewable drafts.

## Important security status
**The static Company HQ, Marketing Studio, and inbox HTML are currently hosted alongside the public site.** `noindex,nofollow` does not protect them. Do not treat their pages as private. The inbox API separately enforces an owner key; never place that key in HTML, JavaScript, a URL, Git, logs, or browser local storage.

The Render HQ service is a public static site. The public HQ dashboard and marketing pages are now transition notices; noindex headers are not authentication. Do not put owner secrets or internal telemetry in static HTML. The owner inbox must be served only behind server-enforced access or remain available solely through the owner-key-protected Worker API. Verify access from a fresh unauthenticated browser before marking privacy complete.

## Local checks
Use Python 3.11 and Node.js 22 or later.

```bash
python -m compileall -q company tests
python -m unittest discover -s tests -v
node --input-type=module --check < worker/index.js
```

The last command may require using `node --check worker/index.js` depending on Node's module configuration. CI is the authoritative check for this repository.

## Required production release checks
1. Confirm the latest Company Quality Gate is green.
2. Confirm the Worker deployment workflow is green and the API's configured origin matches the public site's exact origin.
3. Verify registration/login, successful authenticated intake, rejection of anonymous intake, and preservation of a draft through login.
4. Verify owner inbox reads and status/deletion actions reject requests without a valid owner key.
5. Verify Resend delivery only if a verified sender/domain and secret are configured; a successful API response alone is not proof an email reached the inbox.
6. Verify the public site and client login remain accessible after any security changes.
7. Verify the HQ, Marketing Studio, and owner console deny anonymous access after the private deployment/access boundary is enabled.
8. Use synthetic data for tests and delete it after verification. Never test with real customer data unless explicitly approved.

## What must not be represented as complete without evidence
- Automatic client DMs, marketplace bids, cold outreach, or negotiation.
- Automatic Instagram publishing or DM reading/sending.
- Trusted payment reconciliation or verified revenue tracking.
- General client production deployments without per-project written approval.
- A fully autonomous supervisor/kill switch with tested recovery.
- Private HQ access before a server-enforced access boundary is active.

## Safe operating policy
Agents may discover, rank, draft, generate review bundles, and run tests. External messages, spending, commercial commitments, access to client secrets, production releases, and irreversible finance actions stay disabled unless a specific integration is authorized and tested. Never invent testimonials, outcomes, client approvals, prices, deadlines, or revenue.
