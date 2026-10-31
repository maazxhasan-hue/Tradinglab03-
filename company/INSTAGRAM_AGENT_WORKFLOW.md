# Instagram Agent Workflow for Nexora AI

This is a local, free-first adaptation inspired by [instagram-agent-skill](https://github.com/Jakeschincariol/instagram-agent-skill). It is not a vendored copy of that repository and does not install Claude-specific skills automatically.

## What it does
- Generates seven post/Reel concepts with hooks, timed beat sheets, captions, and review flags.
- Removes common invisible formatting characters from draft text.
- Produces JSON and Markdown artifacts for a human to review.
- Keeps the account choice explicit: `tradinglab03` or `nexora_ai`.

## Run locally
```bash
python company/instagram_content_pack.py \
  --account tradinglab03 \
  --topic "AI trading education" \
  --offer "AI trading course: concepts, Python, backtesting and paper trading" \
  --audience "Indian beginners learning algorithmic trading" \
  --cta "Comment COURSE if you want the syllabus"
```

## Run on GitHub
Open Actions → **Instagram Content Pack (Approval Required)** → Run workflow. Supply the account, topic, offer, audience, and CTA. Download the artifact from the run.

## Guardrails
- Draft-only. It does not post, comment, follow, scrape, DM, or schedule content.
- No claim of profit, guaranteed returns, fake metrics, fabricated clients, or testimonials.
- Validate financial/educational claims before posting.
- No trading code, broker credentials, live trading settings, or private trading infrastructure are touched.
- Metricool is already connected for the TradingLab03 brand, but scheduling/publishing remains a separate explicit approval step. Instagram media must be supplied; text-only Reel drafts cannot be published.
- Use Metricool analytics to assess actual results; do not invent performance numbers.
