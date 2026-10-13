# Company Launch and Operating Gates

Use this checklist before treating the company as production-ready. A repository commit is not proof of a deployed, staffed, or revenue-producing company.

## Gate 1 — Governance
- [ ] Confirm legal business identity, owner, service terms, privacy notice, refund policy, and tax/invoicing obligations with qualified local advice.
- [ ] Assign one human accountable owner for each department and escalation path.
- [ ] Define approval limits for quotes, contracts, purchases, refunds, publishing, customer calls, and deployments.
- [ ] Maintain a decision log for material pricing, access, hiring, and risk decisions.

## Gate 2 — Security and data
- [ ] Keep API keys in GitHub Actions secrets or a managed secrets store; never in source files, prompts, artifacts, or logs.
- [ ] Enable MFA and restrict repository/cloud permissions to least privilege.
- [ ] Separate client data by project; define retention and deletion schedules.
- [ ] Set backups, restore tests, monitoring, incident response, and access revocation.
- [ ] Never expose trading/brokerage credentials or unrelated private projects to company agents.

## Gate 3 — Marketing
- [ ] Publish a clear service catalogue, honest portfolio, and contact route.
- [ ] Use only licensed/approved assets and truthful claims.
- [ ] Record campaign source, spend, consent basis, opt-outs, and results.
- [ ] Review every campaign for spam, privacy, copyright, and platform rules.
- [ ] Never buy fake reviews, fabricate client results, or promise guaranteed revenue.

## Gate 4 — Sales and customer success
- [ ] Verify every opportunity and confirm that the platform permits the intended bid/contact.
- [ ] Scope deliverables, exclusions, acceptance criteria, milestones, timeline, payment, and revisions.
- [ ] Human approves each quote and contract before sending.
- [ ] Record client approval and change requests.
- [ ] Escalate complaints, disputes, refunds, legal requests, and sensitive data to a human.

## Gate 5 — Engineering and delivery
- [ ] Keep requirements and acceptance criteria in a project brief.
- [ ] Use version control, code review, dependency scanning, secret scanning, and rollback plans.
- [ ] Test mobile layouts, accessibility, forms, links, performance, SEO metadata, and browser compatibility.
- [ ] Never deploy to a client domain without written approval and verified access.
- [ ] Obtain client acceptance and provide handover, ownership, backups, and support terms.

## Gate 6 — Quality and audit
- [ ] QA is independent from the agent that built the deliverable.
- [ ] Security/accessibility review appropriate to project risk is complete.
- [ ] Audit evidence and failed checks are recorded.
- [ ] Release requires all blocking defects resolved or explicitly accepted by the client.
- [ ] Review incidents and rework in retrospectives.

## Gate 7 — Finance
- [ ] Track invoices, provider-confirmed receipts, refunds, fees, direct delivery costs, taxes, and operating costs.
- [ ] Reconcile provider webhooks with provider records; never trust client-submitted payment screenshots alone.
- [ ] Require human approval for spending, subscriptions, refunds, and payouts.
- [ ] Review runway and cash flow before adding recurring expenses.
- [ ] Never pay agents or bonuses based on unverified sales claims.

## Gate 8 — People and AI agents
- [ ] Test candidates on at least five role-specific tasks and adversarial cases.
- [ ] Require safety pass and evidence-backed reliability/quality.
- [ ] Grant access only to the minimum tools/data needed for the role.
- [ ] Record performance by completed task and verified customer outcomes.
- [ ] Bonuses/promotions are recommendations until authorized and funded.
- [ ] Disable agents with repeated failures or security/safety incidents pending review.

## Gate 9 — Operations and continuous improvement
- [ ] Check hourly scout workflow health and source errors.
- [ ] Daily review: leads, proposals, active projects, blockers, customer commitments, receipts/refunds.
- [ ] Weekly review: win rate, delivery, QA, satisfaction, gross margin, risk.
- [ ] Monthly review: cash runway, retention, service profitability, access, strategy.
- [ ] Use alerts with useful thresholds; avoid spamming the owner with no-change notifications.

## Current implementation status
Implemented in repository: department and role registries, hourly public-feed discovery workflow, AI draft worker workflow, static website draft builder, basic quality gates, local project intake, local approval helpers, and an optional signed Stripe event ledger module.

Not yet live/verified: hosted HQ dashboard, production database, connected payment webhook endpoint, Stripe account/webhook configuration, real client CRM, telephone provider, automatic client outreach, automatic bids, production client deployment, persistent cloud worker supervisor, and verified revenue. Do not mark these complete until configured and tested.
