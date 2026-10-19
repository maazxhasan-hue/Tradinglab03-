# Client Release Gate — Mandatory Quality Standard

This gate exists to prevent avoidable client complaints. A generated preview or green static check is not proof that the requested system works.

## Release states
- **Draft:** generated locally; may contain placeholders; not client-ready.
- **Internal QA:** every in-scope requirement maps to a reproducible test and evidence.
- **Client review:** internal QA passed; the client can inspect a preview; known limitations are disclosed.
- **Approved release:** acceptance tests passed, authorized approval recorded, production behavior verified, and rollback/handover details ready.
- **Blocked:** any required acceptance test failed, a dependency is missing, or live behavior could not be verified.

Never call work complete, production-ready, deployed, secure, or fully tested without evidence for that claim.

## Before accepting work
- Confirm client identity, goals, deliverables, exclusions, budget, deadline, content ownership, and approver.
- List third-party services, credentials, hosting, personal data, privacy obligations, and recurring costs.
- Confirm actual technical capability and access before promising delivery.
- Record assumptions and unknowns rather than inventing facts, deadlines, prices, testimonials, or results.
- Require human approval before proposals, external messages, commercial commitments, purchases, and production releases.

## Build and QA
For each Version 1 must-have, record a requirement ID, owner, test steps/command, expected result, actual result, status, and evidence.
- Run automated tests and retain their real result.
- Test in a browser and at mobile/narrow viewport sizes.
- Exercise every form, link, navigation path, validation path, loading state, error state, and success state.
- Check keyboard access, visible focus, labels, contrast, and meaningful image alt text.
- Check responsive behavior, browser console/network errors, and critical performance problems.
- For applicable systems, test authorization, authentication, input validation, rate limits, secrets, and privacy.
- Verify each third-party integration against the real service; mocks and static checks are not enough.
- Verify copy, contact details, links, assets, metadata, analytics consent, and legal text.
- Fix failures and rerun relevant tests. Never delete or weaken a failing test merely to get a green result.

## Release and handover
- Every must-have acceptance test passes, or the client explicitly accepts a documented exception in writing.
- A separate QA review checks evidence where feasible.
- Verify preview and production URLs; a deployment success message alone is insufficient.
- Confirm rollback path, monitoring, documentation, access handover, ownership, and support boundaries.
- Obtain explicit approval before production release.
- Deliver a truthful note of tested features, known limitations, access handover, and support contact.
- Record client acceptance, invoicing/payment, and follow-up separately.

## Escalation
If any must-have fails or cannot be tested, mark the release **BLOCKED**, explain why, fix it, and retest. Never hide a defect or silently substitute a demo for a requested feature.

## Current implementation caveat
The current local delivery pipeline generates proposal/scope documents and a static website draft. Its own report marks arbitrary must-have features as needing implementation and acceptance tests, and disables external sending and production deployment. A generated bundle is a review draft, not proof of completed client work.
