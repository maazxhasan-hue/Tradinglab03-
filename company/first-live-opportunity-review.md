# TradingLab03 — Free-First Client Acquisition Pack

**Updated:** 2026-10-15  
**Strategy:** Do not use Freelancer.com. Focus on public, no-subscription sources and direct inbound marketing.  
**Status:** Discovery automation is configured; outreach remains manual and approval-gated.

## Current discovery channels

1. **Reddit r/forhire public RSS** — review posts where buyers request paid services. Use the original post and obey current community rules. Do not automate comments, DMs, or promotional posts.
2. **Codeur public project RSS** — project requests are mainly French-language. Qualify language fit and any platform fees or membership requirements before spending time.
3. **TradingLab03 website/portfolio** — use the existing GitHub Pages site and clearly labelled portfolio concepts to invite inbound enquiries.
4. **Manual direct prospect research** — shortlist small businesses with an observable website problem, then draft a personalized, evidence-based note for owner review. No bulk scraping or unsolicited mass messaging.

## Free-first service offers to test

- One-page landing page or small business website.
- Mobile layout and accessibility cleanup.
- WordPress/Shopify bug-fix or content update, only where the operator can confidently deliver.
- Short-form video and social content packs.
- Simple spreadsheet/report automation.

Start with one narrow offer and one demonstrable sample. Do not promise services that are not deliverable yet.

## Lead handling pipeline

`new → qualified → draft_ready → awaiting_approval → contacted → reply_received → scope_confirmed → contracted → in_progress → QA → delivered → invoiced → paid`

Only the owner can approve a message, quote, deadline, contract, purchase, or external account action. A lead, proposal, invoice, or workflow success is not revenue. Mark a lead paid only after receipt is verified.

## Daily operating routine

- Scan enabled public sources hourly via GitHub Actions.
- Deduplicate leads and keep the original source link.
- Review the ranked shortlist and prepare a tailored draft for eligible direct-client requests.
- Check each source's current rules, project status, eligibility, scope, budget, and payment protections.
- Use one real portfolio example or a clearly labelled concept; never invent client history, testimonials, or outcomes.
- Track replies and delivery obligations only after they actually occur.

## What is not automated yet

- No authenticated CRM, inbox, or social account is connected for direct outreach.
- No AI API key is configured; the draft worker remains in template mode.
- Scheduled workflows are periodic jobs, not a permanently running 24/7 agent.
- No client, contract, or income is confirmed by this document.

## Immediate execution checklist

- [x] Disable all Freelancer.com discovery sources.
- [x] Remove Freelancer API token and SDK dependency from the scout workflow.
- [x] Keep free public RSS sources enabled where previously configured.
- [ ] Inspect the next scout run and its artifact after the config change.
- [ ] Improve the website portfolio with a real, clearly labelled sample offer.
- [ ] Connect any outreach/publishing account only after owner authorization; keep sending approval-gated.
- [ ] Test failure alerts and verify actual scheduled runs.

## Source and safety notes

- Public posts and feeds are leads, not verified buyers.
- Respect the original platform's terms, community rules, and rate limits.
- Never auto-submit applications, send DMs, or make purchases.
- No subscriptions or paid APIs without explicit authorization.
