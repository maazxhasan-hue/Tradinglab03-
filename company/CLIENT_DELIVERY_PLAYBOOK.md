# TradingLab03 Client Delivery Playbook

This playbook standardizes the full client lifecycle: intake → scope → estimate → build → QA → client review → approved release → handover → feedback. It complements the automated draft generator in `company/delivery_pipeline.py`; it does not imply that all features are implemented or that every department/agent is staffed.

## Non-negotiable release controls

- Treat missing details as open questions, never as permission to invent content or requirements.
- Do not invent testimonials, performance claims, client logos, certifications, revenue, prices, or deadlines.
- Do not send proposals/messages, submit bids, make purchases, change prices, or deploy to a client's production environment without explicit human approval.
- Never commit passwords, API keys, access tokens, private client data, or live credentials. Use approved secret storage and least-privilege access.
- A generated website is a review draft until each in-scope requirement has been implemented, tested, and approved.
- Clearly separate Version 1 must-haves from future ideas. Future backlog items are not included in the current quote unless explicitly added.
- Record approval evidence and the person who approved each commercial or release decision.

## Stage 1 — Lead qualification

Capture the public source URL, observed need, date checked, business identity, service fit, and any uncertainty. Public listings are leads, not verified contracts. Follow source/platform rules. The opportunity scout is discovery-only and must not automatically bid, message, or spend.

**Lead status:** New → Researching → Qualified → Needs clarification → Not a fit → Client discussion approved → Won/Lost.

Qualification checklist:
- [ ] Source URL and observation date recorded
- [ ] Need is grounded in evidence, not assumed
- [ ] Service fit and likely deliverables identified
- [ ] Budget/deadline not invented
- [ ] Outreach remains blocked until a human approves it

## Stage 2 — Client intake

Record:
- Business name and primary contact/decision maker
- Business goals, audience, geography, and desired user action
- Existing site/assets and approved design references
- Required pages, screens, deliverables, and functions
- User roles, data handled, integrations, and third-party dependencies
- Accessibility, mobile, privacy, security, analytics, SEO, and language needs
- Budget range, requested deadline, maintenance/support expectations
- Client content owner and approvers for scope, copy, design, and release

Use the companion questionnaire in the downloadable delivery pack. Do not place credentials in intake documents.

## Stage 3 — Requirements and scope

Give each requirement an ID and classify it:
- **V1 Must-have:** required for acceptance
- **Should-have:** useful but not launch-blocking
- **Future:** separate backlog/phase
- **Excluded:** explicitly not part of this engagement
- **Open:** requires client clarification

For each requirement record: description, user/value, inputs/outputs, acceptance test, owner, dependency, status, and evidence. State assumptions and exclusions in plain language.

### Content readiness gate

Track approval for business name, tagline, services, contact details, logo/images, testimonials/claims, legal/privacy content, and SEO metadata. Optional intake fields may be absent in a draft, but missing public-facing details must remain visible as gaps. Do not publish placeholders as final content.

## Stage 4 — Proposal and estimate

A human owner reviews and approves any quote before sending. The proposal should include:
- Client goal and confirmed solution
- Deliverables and acceptance evidence
- Milestones, dependencies, and client responsibilities
- Price/currency, taxes, payment milestones, quote expiry, third-party costs
- Included revisions, support period, and exclusions
- Change-request process, ownership/licensing, and handover expectations

Never auto-fill a price or delivery date unless the owner has approved the values. If a requirement is unclear, mark the estimate provisional and state the assumption.

## Stage 5 — Build and change control

Build only against the approved scope. Keep a traceability table linking requirement IDs to implementation and tests. For out-of-scope requests, create a change request and estimate scope, cost, schedule, risk, and regression-test impact. Start only after approval.

## Stage 6 — Quality assurance

Minimum checks, as applicable:
- [ ] Each approved requirement has a passing acceptance test or a documented blocker
- [ ] Navigation, links, CTAs, forms, validation, error/loading/empty states work
- [ ] Mobile, tablet, and desktop layouts reviewed
- [ ] Keyboard focus, labels, contrast, and image alt text reviewed
- [ ] Approved copy/contact details used; no fabricated claims or unlicensed assets
- [ ] Build/runtime errors and broken assets checked
- [ ] Integrations tested only with authorized test credentials
- [ ] Privacy/security implications reviewed for data-handling features
- [ ] Known limitations, deferred items, and test evidence recorded
- [ ] Critical defects resolved before acceptance/release

A smoke test or green CI workflow confirms only the checks it actually runs; it does not prove every client-specific feature works.

## Stage 7 — Review and release

1. Generate the review bundle and quality report.
2. Share the draft only after the owner approves the client communication.
3. Capture client feedback and map each item to an in-scope defect, approved change, or future idea.
4. Re-test fixes and regression areas.
5. Record client acceptance.
6. Obtain separate, explicit human approval for production deployment.
7. Confirm backup/rollback plan and authorized production credentials before release.

Default state is **review only**. No deployment is implied by a successful build or artifact upload.

## Stage 8 — Handover

Supply the agreed source files/repository, build/run instructions, environment-variable names (never secret values), deployment/domain ownership details, admin instructions, third-party dependencies, test/acceptance evidence, known limitations, backup/rollback plan if applicable, and support terms.

Transfer access securely, verify client ownership/control of accounts, rotate/revoke temporary credentials, and use least privilege. Record the client acceptance and handover date.

## Stage 9 — Feedback and repeat business

After delivery, ask for feedback with owner approval. Record issues, lessons, client satisfaction, and a follow-up owner/date. Offer only relevant optional work—maintenance, content updates, analytics review, or a scoped next phase—without automated unsolicited outreach. Obtain permission before using a client quote, logo, or case study.

## Standard status model

`intake → requirements_review → scope_approved → estimate_approved → build → QA → client_review → acceptance_recorded → release_approved → handover_complete → feedback`

A stage must not be skipped just to make the dashboard look complete. Use `blocked` with a named blocker and owner when approvals, content, access, or tests are missing.

## Completion definition

A delivery is complete only when:
1. The approved scope and exclusions are recorded.
2. Each in-scope requirement is implemented or explicitly documented as blocked/changed with approval.
3. QA evidence exists and critical defects are resolved.
4. Client acceptance is recorded.
5. Production release is separately approved if applicable.
6. Handover, access, support terms, and known limitations are documented.

A template pack or successful automated draft is a useful starting point—not proof of a completed client project.


## Agent execution standard

Follow [Agent Execution Policy](AGENT_EXECUTION_POLICY.md). Agents should complete all agreed, feasible in-scope work without unnecessary objections: inspect context first, decompose the job, resolve routine choices, implement real functionality, test it, fix failures, and continue independent work when a dependency is missing. Escalate only material client decisions, external dependencies, authorization/safety/legal issues, or actions that require approval. A draft or plan is not a completed deliverable; every requirement needs a status and evidence.
