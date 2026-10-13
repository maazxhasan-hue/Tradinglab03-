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
GitHub Actions runs `.github/workflows/hourly-opportunity-scout.yml` hourly and saves a downloadable report artifact. Configure approved public RSS/Atom feeds in `config/opportunity_sources.json`. The initial configured sources are public Upwork search RSS endpoints; if they block access or change format, the run will report source errors. Listings are leads, not guaranteed paid contracts. The system does not auto-apply or message clients.

## Additional revenue agent
Business Intelligence & Revenue Scout analyzes evidence-backed business needs, maps them to services, and drafts a relevant proposal/conversation. It does not send it. Payment verification, invoicing/payment processor integration, connected LLM agents, and telephony remain future integrations.

## Course marketing facts
Course: Build Your Own AI Trading Bot; ₹999; 12 modules, practical project, workbook/materials. Course page: https://trading-agent-35.indiasouthcentral.cloudapp.azure.com/course/. Educational scope: AI trading concepts, Python, backtesting, paper trading. Never promise profit/returns, fabricate testimonials or performance metrics, or imply access to a private trading bot.

## Safety
No brokerage credentials or private trading infrastructure access. No autonomous spending, purchases, refunds, price changes, unsolicited bulk calling, fake claims, or deletion of user data/infrastructure.
