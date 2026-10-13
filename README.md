# BotLab Business Universe

Standalone business automation starter for course marketing and a bounded AI-assisted development team. This repository is separate from any trading-engine repository and must not connect to private trading infrastructure.

## Product facts for drafts
- Course: Build Your Own AI Trading Bot
- Price: ₹999
- Includes: 12 modules, practical project, workbook/materials
- Course page: https://trading-agent-35.indiasouthcentral.cloudapp.azure.com/course/
- Educational scope: AI trading concepts, Python, backtesting, paper trading
- Never promise profit/returns, fabricate testimonials or performance metrics, or imply access to a private trading bot.

## Run locally
Python 3.11+, standard library only:
```bash
python -m unittest discover -s tests -v
python -m botlab
```

## Current MVP
- Draft content generation, claim screening, grounded FAQ answers and human approval states.
- Local job coordinator with idempotent IDs and explicit state transitions.
- 14-role development-team registry and release gate.
- Configurable earn-or-shutdown decision based only on verified, non-refunded receipts.
- No publishing, outbound messages, purchases, payments, website edits, brokerage access, or cloud shutdown is wired.

## Earn-or-shutdown defaults
30-day grace period + 30-day evaluation period; target ₹999 verified net revenue by day 60. If the target is missed, the decision engine returns SHUTDOWN and disables new jobs/external actions in its decision output. This is not a live kill switch or payment verifier. Connect a trusted payment ledger and process supervisor only after explicit approval.

## Team roles
Product Lead, Architect, Research Engineer, Backend Engineer, Frontend Engineer, AI/Agent Engineer, QA Engineer, Security Engineer, Content & Media Producer, SEO & Growth Analyst, Customer Support Analyst, Finance & Revenue Analyst, Release Manager, Independent Red-Team Reviewer.

All external integrations must be opt-in, allowlisted, tested, and disabled by default. Marketing agents must never receive brokerage credentials. No autonomous spending, price changes, refunds, self-replication, or deletion of user data/infrastructure.
