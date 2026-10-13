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
The GitHub Actions workflow `.github/workflows/hourly-opportunity-scout.yml` runs hourly and uploads a report artifact. It reads public RSS/Atom sources configured in `config/opportunity_sources.json`, scores listings, and marks every listing as unverified until a human checks it. It does not apply for jobs or contact clients.

## Business Intelligence & Revenue Scout
The new `company/business_intelligence.py` agent maps observed business needs to service opportunities and creates a draft conversation. It does not invent needs or contact prospects automatically.

## Hiring and performance
Candidates need at least five role-specific test tasks and a passing safety review. Bonus/promotion recommendations are based on quality, reliability, customer rating, completed work, and safety. Humans approve hiring and compensation; agents cannot pay themselves.

## Client voice
A professional feminine voice can be configured in a future voice provider. The agent must disclose it is AI, answer from approved facts, and escalate quote/contract decisions. Calling requires approved contacts, lawful basis/consent checks where applicable, approved purpose/time window, and operator authorization. No telephony is connected now.

## Earn-or-shutdown
The current decision engine uses a default 30-day grace + 30-day evaluation window and ₹999 verified, non-refunded revenue target. It is not a live process or cloud kill switch and cannot receive/verify money on its own.

## Safety
No autonomous spending, paid subscriptions, refunds, price changes, bulk outreach, fake claims, or customer-domain deployment. No brokerage credentials or private trading infrastructure access.
