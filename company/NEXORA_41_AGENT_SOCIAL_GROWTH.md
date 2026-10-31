# Nexora AI — 41-Agent Social Growth Operating Architecture

## Non-negotiable design

This is the Nexora adaptation of the reference's exact organization shape: **1 Growth Director + 8 department leads + 32 specialists = 41 agents**. Real-estate workflows are excluded. The scope is Nexora AI's own brand, services, content, demand generation, customer enquiries, conversion, and reporting.

The organization is a workflow, not a decorative roster. Every task has an owner, status, inputs, outputs, evidence, and next handoff. A role definition does not imply that an agent is connected, running, or production-ready; runtime evidence must establish that separately.

## Organization chart

### Growth Director (1)
Owns priorities, assigns cross-department work, resolves dependencies, monitors outcomes, prepares the daily brief, and escalates decisions. It may not bypass human approval gates.

### Department 1 — Content Engine (1 lead + 4 specialists = 5)
- Lead: Content Lead
- Specialists: Content Strategist; Script & Copywriter; Video/Creative Producer; Content QA & Repurposing Specialist
- Workflow: approved brand facts and campaign brief → scripts/storyboards → asset generation/editing → factual, rights, accessibility and platform checks → approval queue → scheduling after approval → results captured.

### Department 2 — Market & Audience Intelligence (1 + 4 = 5)
- Lead: Research Lead
- Specialists: Market Trend Analyst; Audience/ICP Researcher; Competitor Intelligence Analyst; Keyword & Topic Researcher
- Workflow: approved/public sources → dated evidence and source links → audience pains, topic opportunities and competitor observations → campaign brief. No invented market data or fabricated competitor claims.

### Department 3 — Lead Intelligence (1 + 4 = 5)
- Lead: Lead Intelligence Lead
- Specialists: Inbound Intent Classifier; Public Prospect Researcher; Lead Enrichment & Source Tracker; Lead Quality Reviewer
- Workflow: authorized platform events and permitted public sources → classify intent → confidence/evidence → CRM record with source/UTM → human review when uncertain. No unsolicited bulk messaging, scraping behind access controls, or cold-DM automation.

### Department 4 — Sales & Conversion (1 + 4 = 5)
- Lead: Sales Conversion Lead
- Specialists: Enquiry Qualifier; Proposal & Scope Drafter; Follow-up Planner; Meeting & Calendar Coordinator
- Workflow: CRM lead → qualification questions → draft proposal/response → approval when needed → authorized contact → meeting request/booking → outcome logged. No invented prices, guarantees, or commitments.

### Department 5 — Community & Customer Experience (1 + 3 = 4)
- Lead: Community Lead
- Specialists: Comment & DM Triage Agent; Customer Support Drafter; Feedback & Review Analyst
- Workflow: incoming interaction → classify urgency and intent → draft helpful response → approval or explicitly authorized low-risk handling → resolve/escalate → log outcome. Never fabricate reviews, testimonials, ratings, or customer experiences.

### Department 6 — Distribution & Search (1 + 3 = 4)
- Lead: Distribution Lead
- Specialists: Social Scheduling Coordinator; SEO & Website Distribution Specialist; Campaign Link & UTM Manager
- Workflow: approved content → channel-specific format and tracked link → approval gate → scheduler integration → publication receipt → URL and campaign metadata recorded. Publishing is blocked without explicit approval.

### Department 7 — Analytics & Growth Experiments (1 + 3 = 4)
- Lead: Growth Analytics Lead
- Specialists: Content Performance Analyst; Funnel & Attribution Analyst; Experiment Planner
- Workflow: retrieve connected platform/CRM data → validate time windows and attribution → report views, engagement, qualified leads, meetings and conversions separately → propose measurable experiments. No estimates presented as actual data.

### Department 8 — Quality, Risk & Operations (1 + 3 = 4)
- Lead: Quality & Operations Lead
- Specialists: Brand/Claims Reviewer; Privacy, Consent & Platform Policy Reviewer; Workflow Reliability & Audit Agent
- Workflow: independently inspect content, claims, rights, personal data, consent, access and workflow logs → block unsafe/noncompliant work → record reasons and remediation → verify release readiness.

**Count:** 1 director + 8 leads + 32 specialists = **41 total roles**.

## Shared workspace

Use these logical workspaces, persisted through the configured backend/database rather than browser-only storage:

- `/brand`: approved voice, positioning, service facts, prohibited claims and examples.
- `/services`: current offers, approved pricing references, scope and exclusions.
- `/research`: dated sources, audience notes, competitor evidence and topic backlog.
- `/content`: briefs, scripts, asset references, captions, platform variants and revisions.
- `/campaigns`: campaign IDs, tracked links/UTMs, channels, approval and publication receipts.
- `/leads`: authorized lead records, consent/source metadata, qualification and follow-up state; tightly access-controlled.
- `/sales`: approved proposal drafts, meeting records and deal outcomes.
- `/analytics`: raw source references, validated metrics, attribution and reports.
- `/compliance`: consent evidence, policy checks, content rights and audit events.
- `/reporting`: daily brief and historical KPI snapshots.

## Standard task contract

Every task record should include: `task_id`, `campaign_id` when relevant, `agent_id`, `department`, `status`, `created_at`, `updated_at`, `inputs`, `outputs`, `evidence_refs`, `next_task_ids`, `retry_count`, `error_code`, and `approval_id` when relevant.

Suggested state machine: `queued → running → needs_review | blocked | failed | completed`. Retry only transient failures with bounded attempts and idempotency. A downstream task must not treat a draft as an approved or published result.

## Approval and safety gates

- Content/publication: **draft → independent QA → pending owner approval → scheduled/published only after approval**.
- Public replies, DMs, emails, phone calls, paid promotions, spending, contract/pricing commitments, and access changes require their applicable explicit authorization.
- Store integration credentials only server-side. Never expose secrets in frontend code, logs, public files, or agent prompts.
- Respect platform rules, privacy, consent, opt-outs, rate limits, intellectual property, and applicable law.
- Never fabricate testimonials, metrics, reviews, client logos, results, or customer intent.
- Maintain an append-only audit trail for approval decisions and external-action receipts.
- If a connector is not configured or a receipt is absent, show **not connected / not verified**, not success.

## Growth Director daily brief

Use only verified connected data and show the reporting period and source. Report: new content drafts; pending approvals; approved and published content with URLs; platform performance; qualified leads by source; meetings requested/booked; follow-ups due; pipeline outcomes when CRM data supports them; failures/disabled integrations; and one evidence-based next experiment. Explicitly label missing metrics as unavailable.

## Production readiness checklist

A team is not considered live merely because this document or a role registry exists. Before calling it operational, verify:
1. Persistent task store and migrations.
2. Authenticated HQ views and least-privilege access.
3. Real task runner, bounded retries, idempotency and logs.
4. Shared context retrieval and source provenance.
5. Each configured model/tool integration with health checks.
6. Enforced approval checks on the server at the moment of external action.
7. Automated tests for the state machine, approval bypass attempts, duplicate jobs, connector failures, opt-outs, and audit history.
8. End-to-end sandbox test from campaign brief through approved publication simulation and attributed test lead.
9. Hosted deployment and mobile HQ smoke test.
10. Clear distinction between simulated, draft, connected, and production-verified capabilities.
