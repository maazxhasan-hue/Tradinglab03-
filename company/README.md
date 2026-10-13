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


## AI task worker
`.github/workflows/agent-worker.yml` can run an explicitly requested AI draft task. Add `OPENAI_API_KEY` in repository Settings → Secrets and variables → Actions. Optional `OPENAI_MODEL` and `OPENAI_BASE_URL` are supported by local runs. The worker supports only proposal drafts, website copy drafts, and opportunity summaries; it cannot execute shell commands, publish, contact clients, or spend money. The workflow is manual dispatch only and uploads the draft as an artifact.

## Website build pipeline
`.github/workflows/website-draft.yml` builds a static website draft from the provided brief and runs simple quality checks. It uploads HTML and a QA report as an artifact. It does not deploy the site. Browser testing, security review, accessibility review, client approval, and deployment configuration remain required.


## Full company operating system
- `departments.json` defines 15 functional departments, missions, and teams.
- `roles.json` lists specialist roles across the departments.
- `scorecards.json` defines hourly, daily, weekly, and monthly operating metrics.
- `RELEASE_GATES.md` contains launch gates for governance, security, marketing, sales, delivery, QA, finance, people, and operations.
- `operating_controls.py` blocks sensitive actions without separate approval and defines evidence thresholds for promotion/bonus review.

The department structure is a blueprint. It does not mean human employees have been hired, every AI worker is connected, or the company is production-ready.
