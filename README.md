# BotLab Business Universe

Standalone business automation starter for AI-assisted digital services. This repository is separate from any trading-engine repository and must not connect to private trading infrastructure.

## Start here
- **Company dashboard:** [dashboard/index.html](dashboard/index.html)
- **Company operating plan:** [company/OPERATING_PLAN.md](company/OPERATING_PLAN.md)
- **Agent roles:** [company/roles.json](company/roles.json)
- **Hourly opportunity scout:** [company/opportunity_scout.py](company/opportunity_scout.py)
- **Business Intelligence & Revenue Scout:** [company/business_intelligence.py](company/business_intelligence.py)
- **Run tests:** `python -m unittest discover -s tests -v`
- **Run local content draft:** `python -m botlab`

## Hourly work discovery
GitHub Actions runs `.github/workflows/hourly-opportunity-scout.yml` hourly and saves a downloadable report artifact. Configure approved public RSS/Atom feeds in `config/opportunity_sources.json`. Current sources are We Work Remotely programming/design/sales-marketing feeds and Remotive's public feed. These often list employment roles, not freelance projects; the scout labels results as unverified leads and does not auto-apply. Listings are leads, not guaranteed paid contracts. The system does not auto-apply or message clients.

## Additional revenue agent
Business Intelligence & Revenue Scout can analyze a single public HTTPS homepage for visible SEO, mobile, heading, image-accessibility, and contact-path signals, map observed signals to services, and draft a proposal/conversation. It does not send it. Payment verification, invoicing/payment processor integration, connected LLM agents, and telephony remain future integrations.

## Course marketing facts
Course: Build Your Own AI Trading Bot; ₹999; 12 modules, practical project, workbook/materials. Course page: https://trading-agent-35.indiasouthcentral.cloudapp.azure.com/course/. Educational scope: AI trading concepts, Python, backtesting, paper trading. Never promise profit/returns, fabricate testimonials or performance metrics, or imply access to a private trading bot.

## Safety
No brokerage credentials or private trading infrastructure access. No autonomous spending, purchases, refunds, price changes, unsolicited bulk calling, fake claims, or deletion of user data/infrastructure.


## AI draft worker and website builder
- **AI worker:** [Run manually in GitHub Actions](https://github.com/maazxhasan-hue/Tradinglab03-/actions/workflows/agent-worker.yml). Add repository secret `OPENAI_API_KEY` first. It generates drafts only and uploads an artifact.
- **Website draft builder:** [Run manually in GitHub Actions](https://github.com/maazxhasan-hue/Tradinglab03-/actions/workflows/website-draft.yml). It builds a static site and quality report for download; it does not deploy to a client's domain.
- **Local website build:** `python -m company.website_pipeline --brief config/website_brief.example.json --output data/website_drafts/example`
- **Local AI task queue:** `python -m company.agent_runtime --task-type summarize_opportunity --title "Review listing" --context "Paste a public listing here"`, then `python -m company.agent_runtime --run-one` (requires `OPENAI_API_KEY`).
