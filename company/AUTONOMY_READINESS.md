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

## Web operations access-control audit — 17 October 2026

### Current exposure and required fix

- The public marketing site and client login/project-intake flow are intended to remain public.
- `dashboard/index.html` (Company HQ), `dashboard/marketing.html` (Marketing Studio), and `dashboard/inbox.html` are static files in the same public website/repository. Their `noindex,nofollow` metadata only asks search engines not to index them; it is **not authentication** and does not stop a visitor from opening the URL or reading the page source.
- The owner inbox's enquiry API is separately protected by the server-side owner key. Never move that key into HTML, JavaScript, a URL, or browser storage.
- The current Vercel project serves the public site and these static pages together. Enabling project-wide deployment protection could also block public client access, so it must not be switched on blindly as a workaround.

### Release gate for a genuinely private HQ

1. Keep client-facing pages and the public homepage on the public deployment.
2. Move Company HQ and Marketing Studio to a separate owner-only deployment or put them behind a server-enforced access layer (for example, Cloudflare Access on a controlled domain, or an authenticated server route). Static JavaScript-only passwords are not an acceptable security boundary.
3. Keep the inbox API's owner-key authorization independent of the HQ page gate; verify unauthenticated reads, status changes, and deletes return 401/403.
4. Verify that the public site, login, and authenticated intake still work after the split; then verify the HQ URLs deny anonymous access from a fresh browser.
5. Until these tests pass, label the HQ as an operational console with public-page exposure—not as a private or secured dashboard.

No owner credentials or production settings should be guessed or embedded in the repository to make this gate appear complete.

## Expanded agent capability audit — 17 October 2026

The operating target is an agent-run service business, with evidence-based checkpoints and a clear record of what is and is not autonomous. Agents should complete all permitted internal work without repeatedly asking the owner to do manual research; external side effects still require a connected, authorized integration.

### Work agents should handle automatically

1. **Discovery and source health:** poll only enabled, permitted feeds on the configured schedule; record fetch errors, last-success time, duplicates, and source coverage. Keep RequestSignals and Project Mela manual-only until their official feeds/APIs and terms are verified.
2. **Qualification:** separate direct buyers from employee vacancies, freelancers advertising services, stale/closed requests, AI-prohibited briefs, scams, and paid-platform-only leads. Preserve original URL and evidence; never infer a client exists from a search snippet.
3. **Service matching:** map each suitable request to an available offer (business website, landing page, website audit, SEO/content, short-form content, or business automation) and list capability gaps.
4. **Proposal pack:** draft a specific, truthful response, suggested scope, questions, exclusions, and estimate assumptions. Never invent case studies, client results, price approval, or delivery dates.
5. **Demo and delivery:** create a concept/demo in a separate workspace; wait for a written client brief and agreed scope before production work. Run automated checks and a separate QA pass, document limitations, and produce handover notes.
6. **Client success:** once a permitted inbound message/reply connector is connected, classify the reply, summarize needs, draft a response, and update the pipeline. No authenticated outbound messaging connector is verified today.
7. **Marketing:** prepare post drafts, assets, and a schedule; use a connected publishing service only after the correct brand/account and publishing authorization are confirmed. Posting must respect platform rules and avoid fabricated claims.
8. **Finance and learning:** track agreed quotes, expenses, fees, verified receipts, refunds, and net margin. Draft invoices/retrospectives only from confirmed data; do not treat leads, views, or sent proposals as revenue.
9. **Supervisor:** report workflow failures, stale source data, missing credentials, and blocked steps; never silently mark a failed step complete.

### Acceptance criteria for claiming autonomy

- Every stage writes a durable record with timestamp, source/brief reference, status, and error or evidence.
- Re-runs are idempotent: no duplicate leads, duplicate messages, or repeated deployments.
- External actions are disabled by default unless a specific integration is authenticated, allowed by platform terms, and explicitly enabled for that action.
- No secrets are written to the repository, logs, artifacts, prompts, or client deliverables.
- The end-to-end synthetic test passes without claiming a real client; live tests separately verify real account access and delivery.
- A failure stops dependent stages, preserves artifacts, and surfaces the exact blocker.
- Only owner-approved scope, price, terms, production deployment, and irreversible business actions may cross their respective gates.

### Current verified blockers and next actions

| Blocker | Action |
|---|---|
| Narrow discovery coverage | Keep the hourly scout, review disabled sources only after their access and terms are checked, and manually inspect approved public lead indexes |
| Source quality / stale listings | Require original-post verification before a lead becomes actionable |
| No authenticated outbound DM / marketplace integration | Do not claim autonomous outreach. Connect a supported account and verify its permitted write actions before enabling messages |
| Model-based work depends on OPENAI_API_KEY and quota | Use deterministic templates when unavailable; run model work only when an approved key and budget are available |
| Client production access is project-specific | Obtain written scope, client-owned credentials, and release approval per project |
| Payments not reconciled automatically | Record revenue only from a trusted payment record and track fees/refunds |
| Workflow schedules can be delayed | Check latest run state and artifact timestamps; a configured cron is not proof of a successful execution |

### Current prospect — House of Payal

- The concept file is committed at `dashboard/demos/house-of-payal-concept.html`; it is an independent demo and not an approved brand site.
- The deploy workflow for the concept commit reported success at https://github.com/maazxhasan-hue/Tradinglab03-/actions/runs/38957491074. The exact published URL was not independently confirmed here.
- A tailored outreach draft exists in the conversation; no outbound message, reply, signed scope, or revenue is recorded.
- The next permissible steps are to verify that the request remains open, send only through a connected and authorized channel, then create the production brief after the buyer agrees.

**Truthful current state:** discovery, qualification logic, proposal generation, demo creation, delivery workflows, and scheduled health checks exist in code. Fully autonomous client contact, negotiation, payment, and general production deployment are not yet verified.
