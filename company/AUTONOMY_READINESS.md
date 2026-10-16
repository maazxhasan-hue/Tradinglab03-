# TradingLab03 Autonomy Readiness — 16 October 2026

## Honest status

TradingLab03 is a partially automated service-business toolkit, not a fully autonomous sales company. The public website and enquiry API were previously smoke-tested; repository code contains opportunity discovery, lead scoring, proposal/client-pack generation, a bounded tool-using agent, specialist orchestration, and a client-delivery draft workflow. The existence of code or a green build does not prove every scheduled run, model call, production integration, client message, deployment, or payment path works end to end.

## Current capability map

| Stage | Current implementation | Verified status / remaining gate |
|---|---|---|
| Public project discovery | `company/opportunity_scout.py`, allowlisted RSS/Atom feeds, hourly GitHub Actions workflow | Discovery-only. Inspect the latest successful Actions run and artifact; public feeds can fail or contain stale/noisy listings. |
| Lead classification | Buyer-intent, contract, job-vacancy, and disqualifier scoring | Unit tests exist. Keep the human review gate for source legitimacy, eligibility, terms, budget, and recency. |
| Business website observations | `company/business_intelligence.py` | Produces evidence-based service hypotheses and drafts; no automatic outbound contact. |
| Proposal and client pack | `company/client_pipeline.py`, proposal-pack workflow | Drafts only. Price and deadline must be approved by the owner. |
| Project delivery drafts | `company/delivery_pipeline.py`, `company/autonomous_delivery.py`, client-delivery workflows | Can generate review bundles from an explicit brief. Generated output is not proof of production readiness; run tests and review the bundle. |
| AI tool / specialist pass | `company/tool_agent.py`, `company/specialist_orchestrator.py` | Bounded workflow exists. Model access, quota, output quality, and the latest successful live run must be verified separately. |
| Client messaging / negotiation | No verified authorized outbound integration | Not autonomous. Do not automate DMs, bids, platform messages, calls, or promises. |
| Client-facing production deployment | No verified general client deployment authorization | Requires project-specific credentials, approved scope, security review, owner approval, and release checks. |
| Invoice/payment collection and reconciliation | No verified payment processor or trusted reconciliation integration | Not autonomous. Only count revenue after independently verified receipt and refund check. |
| Agent self-funding / purchasing | Not implemented | No purchases, subscriptions, ads, or paid applications. |
| Monitoring and kill switch | Workflow logs and health checks exist; complete business-level supervisor is not proven | A durable kill switch, service supervision, alerts, and failure recovery require explicit tests before claiming autonomy. |

## Required operating policy

1. **Free-first:** do not enable paid APIs, paid lead sources, ads, subscriptions, paid applications, or purchases without a separate explicit owner decision.
2. **No outbound automation:** discovery and draft generation are allowed; external contact is not. Do not add automated DMs, bids, cold email, or calling.
3. **Truthful sales:** never invent client results, testimonials, credentials, delivery capacity, prices, or deadlines.
4. **Contract gate:** no implementation begins until the buyer's requirements, deliverables, exclusions, acceptance criteria, payment milestones, ownership, and timeline are agreed in writing.
5. **Least privilege:** client credentials are project-specific, never placed in prompts or logs, and not reused across clients. Do not access unrelated private or trading infrastructure.
6. **QA and release gate:** run regression tests; inspect the deliverable; test mobile/accessibility/security/link/form behavior as relevant; document known limitations; get client approval before production release.
7. **Payment truth:** do not mark a sale won or revenue earned from a message, verbal promise, invoice, screenshot alone, or generated report. Record a receipt only after a trusted payment record is checked; track refunds and fees.
8. **Stop safely:** any uncertain identity, unclear authorization, suspicious payment, request for secrets, unexpected cost, failing tests, or scope creep pauses the affected action and requests owner review.

## First real end-to-end validation

Use a real buyer only after the owner approves the project. Until then, validate with synthetic data:

- [ ] Run `python -m unittest discover -s tests -v` in GitHub Actions.
- [ ] Trigger the opportunity scout and inspect its artifact, source errors, candidate URLs, deduplication, and buyer-intent decisions.
- [ ] Run the bounded client-execution workflow with a clearly labelled synthetic brief; verify traceability and QA artifacts are uploaded.
- [ ] Confirm the public enquiry form still writes to the owner inbox and unauthorized reads/deletes are rejected.
- [ ] Confirm no workflow sends messages, creates bids, publishes to social accounts, spends money, deploys a client site, or marks revenue.
- [ ] For a real project, test the whole flow manually with owner approval at each commercial, credential, release, and payment boundary.

## Definition of "autonomous"

Do not call the company fully autonomous until every required stage has repeatable evidence from a controlled end-to-end test: discovery, qualification, authorized communication, signed scope, bounded execution, independent QA, client-approved delivery, trusted payment reconciliation, audit trail, alerting, and safe stop/recovery. In the current configuration, communication, commercial commitments, production release, and payment reconciliation remain owner-operated or unintegrated.

## Links

- [Repository](https://github.com/maazxhasan-hue/Tradinglab03-)
- [GitHub Actions](https://github.com/maazxhasan-hue/Tradinglab03-/actions)
- [Opportunity source policy](OPPORTUNITY_SOURCE_POLICY.md)
- [Free-first acquisition plan](free-first-acquisition-plan.md)
- [Client delivery playbook](CLIENT_DELIVERY_PLAYBOOK.md)
