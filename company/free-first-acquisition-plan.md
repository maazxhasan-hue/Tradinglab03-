# TradingLab03 — Free-First Client Acquisition Plan

**Status:** Operating guide; no outbound actions are automated.  
**Goal:** Find genuine buyers for small, deliverable digital services without subscriptions, paid proxies, bulk outreach, or fabricated claims.

## Current verified position

- The hourly scout is configured for Reddit r/forhire and Codeur's public project feed.
- The latest reviewed scout result found listings, but the proposal queue had **0 source-policy-eligible projects**. No listing from that run was eligible for proposal drafting under the current rules.
- Codeur is research-only because applying requires a paid plan and commission. Do not pay or submit offers there.
- Reddit is public but noisy. A listing must clearly show a buyer asking for a concrete deliverable; a freelancer advertising services is not a client lead.
- Freelancer.com remains disabled by owner decision. Do not re-enable it.
- No contact email or outbound account is assumed. No messages, bids, or proposals are sent automatically.

## Free-first channels

| Channel | How to use it | Automation status |
|---|---|---|
| Reddit r/forhire | Use the configured public RSS scout. Review each original post, subreddit rules, budget, scope, date, and buyer intent. | Automated discovery; human review required |
| Codeur public project feed | Use only to understand demand, language, and service trends. | Research-only; do not apply or pay |
| [RequestSignals](https://requestsignals.com/) | Browse the public categorized leads manually and open the original post. Verify that the person is asking for a service, the listing is current, and the platform's terms permit the intended response. | Manual-only until an official feed/API and terms are verified |
| [Project Mela](https://www.projectmela.com/) | Review its public gig/project area manually; confirm current account requirements, eligibility, payment terms, and fees before participating. | Manual-only; no account actions automated |

**Important:** Public visibility is not proof of a legitimate buyer, permitted reuse, or a paid contract. Do not scrape login-only pages, bypass access controls/rate limits, or automate messages, bids, comments, or applications.

## Lead qualification checklist

A lead is eligible for human review only when all applicable items are checked:

- [ ] The original listing is reachable and still open.
- [ ] The poster is asking to buy a defined service, not advertising their own services or filling a normal employee role.
- [ ] A concrete deliverable matches TradingLab03's current capabilities.
- [ ] Budget/payment terms, deadline, location/language, and platform eligibility are understood or clearly marked unknown.
- [ ] No upfront-fee scam, unpaid test, suspicious payment request, or unrelated crypto deposit is involved.
- [ ] The original URL, source, date checked, evidence, and uncertainties are recorded.
- [ ] A relevant portfolio sample exists and is honestly labelled as a concept if fictional.
- [ ] Any proposed contact method is allowed by the source/platform and approved by the owner.

Do not invent a budget, private contact details, past clients, testimonials, or results.

## Offer ladder

Start with small scopes that can be completed and tested reliably:

1. **One-page business landing page** — responsive layout, client-approved content, enquiry path, and link/mobile checks.
2. **Website cleanup** — fix a named, reproducible issue on agreed pages and document before/after checks.
3. **Short-form content starter** — hooks, scripts, captions, and editing instructions using client-supplied assets.
4. **Small workflow automation** — only after the data, access, error handling, and acceptance criteria are clear.

Never promise guaranteed sales, SEO rankings, views, or investment returns. Do not quote a price or deadline until the scope and delivery effort are reviewed and approved.

## Manual weekly routine

1. Review the latest scout artifact and source-error report.
2. Open the original URL for every promising listing and complete the qualification checklist.
3. Keep only the strongest, current, buyer-intent opportunities in a shortlist.
4. Create a tailored proposal draft that addresses the actual brief and links to one relevant sample.
5. Review wording, scope, claims, fees, eligibility, and payment protection.
6. Obtain explicit owner approval before sending anything.
7. Record replies and outcomes accurately. Count revenue only after trusted payment confirmation and account for fees/refunds.

## Readiness blockers — do not hide them

- **Contact path:** the public contact email must be supplied/approved before the website's mailto enquiry handoff can be configured.
- **AI model execution:** the last synthetic run skipped model specialists because no usable API key was available. The deterministic workflow remains usable; AI completion is not verified. Do not trigger paid usage without approval.
- **Real client delivery:** the latest successful bundle is synthetic. No real client has been contacted, no payment received, and no production site deployed.
- **Source quality:** no current free-first listing was eligible in the latest queue. Continue permitted discovery and manual research; do not relabel research-only leads as actionable.

## Success metrics

Track qualified buyer-intent leads, owner-approved proposals, replies, accepted scopes, completed acceptance tests, verified receipts, refunds, direct costs, and net margin. Raw listing counts, clicks, draft artifacts, and synthetic tests are not revenue.

## Approval boundaries

This plan authorizes research and drafting only. It does not authorize messages, bids, applications, purchases, subscriptions, public posts, price commitments, client-domain deployment, or changes to unrelated trading/brokerage systems.

## Current manual source check — 2026-10-16

- **RequestSignals:** the public page advertises free browsing without signup and links each item to an original post. It is useful for manual discovery, but no official RSS/API or reuse terms have been verified here, so it remains manual-only. [Browse all leads](https://requestsignals.com/leads).
- **Example checked, not qualified for action:** [“Looking for a Freelance Digital Marketer In India – Healthcare”](https://www.reddit.com/r/InstagramMarketing/comments/1vvycqn/looking-for-a-freelance-digital-marketer-in-india/) asks for paid ads, SEO, and Instagram marketing, but the post is roughly two months old and requires healthcare-marketing experience. Treat it as stale and do not contact without a fresh status check and evidence of fit.
- **Example checked, not qualified for action:** [“Web developer to write me a small presentation web page”](https://www.reddit.com/r/forhire/comments/1whtgg3/hiring_web_developer_to_write_me_a_small/) mentions €100+ but explicitly asks that AI not be used for development. TradingLab03 must not offer AI-built delivery for this request; it is excluded unless the work can genuinely meet that condition.
- **Project Mela:** public gig pages are browseable, but individual entries need freshness and payment/eligibility checks. Keep it manual-only; no registration or bid was made. [Browse gigs](https://www.projectmela.com/gigs).

These examples are research notes, not actionable or verified leads. No person was contacted, and no revenue is claimed.


## Website-to-client workflow (updated 2026-10-16)

- The public project form builds and downloads a structured brief in the visitor\u2019s browser; it does not upload to a server.
- Visitors can copy the brief and open the connected public Instagram profile `@tradinglab03` to paste and send an enquiry manually. The site never claims the enquiry was submitted automatically.
- The HQ links directly to the Instagram inbox and the manual-dispatch `Autonomous Client Execution` workflow. After a client sends an agreed brief, the operator can dispatch the workflow to create a review bundle. The workflow does not automatically read Instagram DMs, send replies, sign contracts, take payment, or deploy client production systems.
- The model-based worker pass requires a valid, quota-available `OPENAI_API_KEY` in GitHub Actions secrets; otherwise the deterministic/template output remains available with limitations. Do not add secrets to repository files or workflow inputs.

## Fresh prospecting check — 2026-10-17

- A fresh public-web search did **not** produce a clearly current, verified buyer request that Nexora AI can safely pursue today. Search results that looked relevant were mostly developers advertising their own services or stale posts; those are not buyer leads.
- The scout's most recent known successful hourly run is documented in GitHub Actions, but a successful scan is not proof of a qualified client. Review its artifact and the current daily review before treating any record as actionable.
- **Immediate next action:** open the latest [Hourly Opportunity Scout run](https://github.com/maazxhasan-hue/Tradinglab03-/actions/workflows/hourly-opportunity-scout.yml), download the newest `tradinglab03-opportunities-…` artifact, then open the original listing for each candidate. Keep only fresh buyer requests from sources whose policy is `review_allowed`.
- **Do not pursue Codeur leads yet:** the source remains `research_only` because proposals require paid access and commission. No purchase or application was made.
- **No outreach was sent:** the connected tools available to this workflow do not provide an authenticated Reddit/marketplace account or an authorized outbound messaging action. Do not claim a client was contacted, a proposal was submitted, or revenue was earned until there is evidence.
- The public portfolio can be shared as capability proof: https://maazxhasan-hue.github.io/Tradinglab03-/dashboard/website.html. Describe demo work as a demo, not a paid client result.

## RequestSignals / live-search follow-through — 2026-10-17

**Decision:** RequestSignals remains a manual research source, not an automated feed. Do not scrape it or treat its index page as a qualified prospect list.

**Research result:** A fresh web search surfaced a recently updated guide describing recent web-design requests, but the examples were summaries without enough direct evidence here to qualify a specific buyer. These are not imported as leads. Search results can be promotional, stale, or incomplete.

**Manual qualification steps**
1. Open [RequestSignals leads](https://requestsignals.com/leads) and select a request matching a service Nexora AI can deliver.
2. Open the original Reddit/X/other post; record its direct URL and post date.
3. Confirm it is a buyer requesting a deliverable, is still open, and does not forbid AI assistance or impose eligibility/experience requirements we cannot meet.
4. Record scope, budget, deadline, platform rules, payment terms, and uncertainties in the private lead tracker. Do not put personal contact details into public repository files.
5. Prepare one specific response draft and check every claim against the portfolio. Do not send it until the owner approves and the platform permits that contact.
6. If no request passes these checks, keep the qualified-lead count at zero; improve the demo rather than inventing a lead.

**Current outcome:** No specific RequestSignals entry has been verified as an actionable buyer during this check. No account was created, no fee paid, no message sent, and no proposal submitted.

## RequestSignals manual lead review checklist — 2026-10-17

RequestSignals advertises a free, no-signup public lead browser with categorized service requests and source links, refreshed about every two hours according to its homepage. This is a third-party claim, not an independent guarantee that every lead is genuine or current. See https://requestsignals.com/ and https://requestsignals.com/leads.

### Run this review before creating a proposal
1. Open the live leads page and choose **Web Development**, **Digital Marketing**, **Shopify & E-commerce**, or **Content Writing** only where the actual brief matches our deliverable.
2. Open each original source post. Record the original URL, date/time checked (UTC), requested deliverable, budget if stated, deadline, and the exact evidence of buyer intent.
3. Reject listings that are stale, closed, self-promotion, a normal employee vacancy, unpaid work, or require a paid platform/subscription we have not approved.
4. Score fit: **3** = explicit buyer request and clear deliverable; **2** = plausible service need but scope unclear; **1** = weak or indirect signal; **0** = not a buyer. Only 3-point leads proceed to proposal drafting after freshness and platform-rule checks.
5. Draft a tailored, truthful response that references the specific need and one relevant demo. Label demos as demos; never invent client results, experience, budget, or a deadline.
6. Keep the draft unsent until the owner has reviewed it and a permitted contact method is available. Record sent/reply/status only when evidence exists.

### Prospect review log
No individual RequestSignals listing has been verified in this update, so no lead is recorded as qualified and no proposal is marked sent. Use this template when reviewing an actual listing:

| Field | Value |
|---|---|
| Original post URL | |
| Source and post date | |
| Date checked (UTC) | |
| Buyer intent evidence | |
| Deliverable / scope | |
| Budget / deadline | |
| Platform eligibility and fees | |
| Fit score (0–3) | |
| Risks / unknowns | |
| Next action | |
| Contact status | Not contacted |

**Current boundary:** public browsing and proposal drafting only. No account was created, no subscription purchased, and no one was contacted.
