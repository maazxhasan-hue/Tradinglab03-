# Nexora AI — Delivery & Release Runbook
Updated: 17 October 2026

This repository contains the public services website, client login/intake flow, Cloudflare Worker API, owner inbox UI, internal workflow pages, marketing drafts, automation workflows, tests, and operational documentation.

## Live entry points
- Public website: https://nexora-ai-sooty-two.vercel.app
- Client project intake: https://nexora-ai-sooty-two.vercel.app/dashboard/website.html
- Client login: https://nexora-ai-sooty-two.vercel.app/dashboard/login.html
- Company HQ: https://nexora-ai-sooty-two.vercel.app/dashboard/
- Marketing Studio: https://nexora-ai-sooty-two.vercel.app/dashboard/marketing.html
- Owner inbox: https://nexora-ai-sooty-two.vercel.app/dashboard/inbox.html
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

An attempt to create a separate Vercel owner-console project failed with a Vercel API `403 Forbidden` scope/authorization error. Do not enable project-wide protection on the public Vercel project: it could block customers from the public website. The proper fix is to deploy owner pages in a separate project with Vercel SSO/deployment protection, or put them behind a server-enforced access layer such as Cloudflare Access on a controlled domain. Verify access from a fresh unauthenticated browser before marking this complete.

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
