# Harvey Worker (Nexora)

A persistent API for prospect discovery, saved prospect records, task history, human-reviewed outreach drafts, and a guarded Resend delivery path.

## Current deployment

The live Render service is `https://tradinglab03.onrender.com`. Its active source is built from the repository root `Dockerfile`, which packages `harvey-worker/app.py`. The separate `harvey-worker/render.yaml` is a Blueprint definition; it does not create another service unless applied in Render.

## Core endpoints

- `GET /health` — service/database status and whether the send feature flag is enabled. This does not prove Resend credentials or inbox delivery.
- `GET /metrics` — authenticated counts.
- `POST /prospects/discover` — authenticated OpenStreetMap listing discovery. JSON: `{"city":"Bengaluru","category":"business","limit":15}`.
- `GET /prospects` — authenticated saved prospects.
- `POST /outreach/draft` — authenticated draft creation. JSON: `{"prospect_id":1,"service":"website improvements","value_proposition":"A concrete value proposition."}`.
- `GET /approvals` — authenticated draft approval queue.
- `POST /approvals/{id}/decision` — authenticated `{"decision":"approve"}` or `{"decision":"reject"}`. Approval alone never sends.
- `GET /tasks` — authenticated task history.
- `GET /email/status` — authenticated Resend configuration status, suppression count, and daily count.
- `POST /email/test-resend` — authenticated self-test only. Requires `{"confirm_send":true}`, `RESEND_API_KEY`, and `RESEND_TEST_RECIPIENT`; limited to three test attempts per UTC day. It uses Resend's onboarding sender and does not send to a prospect.
- `POST /email/send-approved` — authenticated delivery for one explicitly supplied recipient. Requires `{"approval_id":1,"recipient":"recipient@example.com","confirm_send":true}`, a previously approved draft, and all production environment settings below.
- `GET /email/unsubscribe?token=...` and `POST /email/unsubscribe?token=...` — signed unsubscribe endpoint; adds the address to the suppression list.

All protected routes require the `X-API-Key` header. CORS is restricted to configured Nexora HQ origins.

## Required server-side configuration

Never put credentials in the browser or commit them to Git.

- `HARVEY_API_KEY` — required API authentication key.
- `RESEND_API_KEY` — Resend API key stored only in the Render environment.
- `RESEND_FROM_EMAIL` — sender identity from a domain verified in Resend for production outreach. The Resend onboarding sender is for limited testing and is not a production sender for prospect outreach.
- `UNSUBSCRIBE_SECRET` — long, random secret used to sign unsubscribe tokens.
- `EMAIL_SENDING_ENABLED=true` — explicit feature flag; leave unset/false until the sender is verified and configuration is checked.
- `PUBLIC_API_BASE_URL` — public HTTPS base URL used in unsubscribe links; defaults to `https://tradinglab03.onrender.com`.
- `RESEND_TEST_RECIPIENT` — an inbox controlled by the operator for the self-test only.

The production send route fails closed unless the flag, API key, sender, and unsubscribe secret are present. Each send also requires an approved draft and explicit confirmation. It checks suppression, prevents concurrent duplicate sends for the same draft/recipient, and enforces a 20-per-UTC-day limit. Provider acceptance is not the same as inbox delivery; verify delivery in Resend's event log and the recipient mailbox.

## Safety boundaries

Prospect discovery data may be incomplete and must be verified. Do not send unsolicited bulk campaigns. Use truthful, relevant outreach, a verified sender domain, applicable legal compliance, and prompt opt-out handling. The API only sends to the recipient explicitly supplied by the authenticated operator after draft approval and per-send confirmation. A successful provider API response is reported as **accepted**, not guaranteed delivered.

## Local test

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r harvey-worker/requirements.txt
HARVEY_API_KEY=local-test-key DATABASE_PATH=./harvey.db uvicorn app:app --app-dir harvey-worker --reload
```
