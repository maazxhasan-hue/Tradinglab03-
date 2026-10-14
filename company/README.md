# TradingLab03 AI Services Company

A separate operating system for AI-assisted digital services. This is a local-first MVP; live AI workers, telephony, payment processing, and production hosting are not automatically connected.

## Services
- Professional business websites and landing pages
- Website redesign, performance, and accessibility
- SEO and content strategy
- Short-form video scripts, captions, and editing plans
- Customer FAQ/support drafts
- Lead discovery, project qualification, and proposal drafts

## Hourly opportunity discovery
The GitHub Actions workflow `.github/workflows/hourly-opportunity-scout.yml` runs hourly and uploads a report artifact. It reads public RSS/Atom sources configured in `config/opportunity_sources.json` (We Work Remotely and Remotive), scores listings, and marks every listing as unverified until a human checks it. These sources primarily list remote roles, not guaranteed freelance contracts. It does not apply for jobs or contact clients.

## Business Intelligence & Revenue Scout
The new `company/business_intelligence.py` agent maps observed business needs to service opportunities and can call `company/site_audit.py` to inspect a single public HTTPS homepage for basic SEO, mobile, accessibility, and contact-path signals. Findings are heuristic and must be human-verified. It creates a draft conversation but does not contact prospects.

## Hiring and performance
Candidates need at least five role-specific test tasks and a passing safety review. Bonus/promotion recommendations are based on quality, reliability, customer rating, completed work, and safety. Humans approve hiring and compensation; agents cannot pay themselves.

## Client voice
A professional feminine voice can be configured in a future voice provider. The agent must disclose it is AI, answer from approved facts, and escalate quote/contract decisions. Calling requires approved contacts, lawful basis/consent checks where applicable, approved purpose/time window, and operator authorization. No telephony is connected now.

## Earn-or-shutdown
The current decision engine uses a default 30-day grace + 30-day evaluation window and ₹999 verified, non-refunded revenue target. It is not a live process or cloud kill switch and cannot receive/verify money on its own.

## Safety
No autonomous spending, paid subscriptions, refunds, price changes, bulk outreach, fake claims, or customer-domain deployment. No brokerage credentials or private trading infrastructure access.


## Free draft worker
`.github/workflows/agent-worker.yml` runs without paid API credits using a built-in rule-based template mode. Choose a task type, title, and context in the workflow's **Run workflow** form; the resulting draft is uploaded as an artifact. This mode is not a generative AI model: it produces structured starter drafts and checklists only.

For optional model-generated text, set `AI_PROVIDER=openai` and configure `OPENAI_API_KEY` locally. OpenAI API billing is separate from ChatGPT plans and is not required for free template mode. The worker supports only proposal drafts, website copy drafts, and opportunity summaries; it cannot execute shell commands, publish, contact clients, or spend money. The workflow is manual dispatch only.

## Free client proposal pack
`.github/workflows/client-proposal-pack.yml` creates a client-specific proposal and outreach draft without paid APIs. Run it manually, enter a business name, choose a service, and provide a specific need; add evidence only when checked by a human. It produces Markdown and JSON artifacts. Any quote is optional and must be entered by the operator. Nothing is sent, no prospect is contacted, and no work is accepted automatically. Review the scope, pricing, and message before using them.

## Automatic opportunity-to-lead pipeline
The hourly scout runs `company.opportunity_scout` and then `company.opportunity_importer`. The scout records service-keyword matches separately from client-fit qualification. Only high/review listings with explicit freelance/contract signals, no risk flags, and no detected on-site/location restrictions are imported into `data/leads.json`; ordinary employment ads and ambiguous listings are excluded. Duplicate source URLs are skipped. These filters are heuristic, not proof: review the original listing for actual client/project status, country eligibility, payment, scope, legitimacy, and platform rules before acting. Payment is never marked verified automatically. The workflow commits the updated register to `main`; it shares a concurrency group with manual lead updates to reduce write collisions. No outreach or applications are sent.

## Persistent lead tracker
`data/leads.json` is the company lead register. Run `.github/workflows/lead-tracker.yml` manually to add a lead or update its stage; successful runs commit the register back to `main`. Each record keeps evidence, next action, and status history. Paid revenue counts only when an operator sets `paid_verified` and supplies revenue evidence. This is a lightweight JSON ledger, not a CRM service or payment processor. Never put passwords, payment data, private customer details, or secrets into lead notes. The workflow does not contact prospects or send proposals.

## Website build pipeline
`.github/workflows/website-draft.yml` builds a static website draft from the provided brief and runs simple quality checks. It uploads HTML and a QA report as an artifact. It does not deploy the site. Browser testing, security review, accessibility review, client approval, and deployment configuration remain required.


## Full company operating system
- `departments.json` defines 15 functional departments, missions, and teams.
- `roles.json` lists specialist roles across the departments.
- `scorecards.json` defines hourly, daily, weekly, and monthly operating metrics.
- `RELEASE_GATES.md` contains launch gates for governance, security, marketing, sales, delivery, QA, finance, people, and operations.
- `operating_controls.py` blocks sensitive actions without separate approval and defines evidence thresholds for promotion/bonus review.

The department structure is a blueprint. It does not mean human employees have been hired, every AI worker is connected, or the company is production-ready.
