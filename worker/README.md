# TradingLab03 enquiry service

This Cloudflare Worker is a separate business-intake service. It does not connect to trading, brokerage, MCX, or Azure trading infrastructure.

## What it does

- Receives real website enquiries at `POST /api/intake` and saves them to Cloudflare D1.
- Validates input, enforces a strict allowed-origin check, caps request size, uses a honeypot, and rate-limits by a one-way IP hash.
- Sends an email notification through Resend only when all three settings are configured: `RESEND_API_KEY`, `NOTIFY_EMAIL`, and `FROM_EMAIL`. The sender address must be verified with Resend.
- Exposes `GET /health` for a non-sensitive health check.
- Exposes `GET /api/admin/submissions` only with an `Authorization: Bearer ...` owner key. The owner key must never be placed in the public website.
- Stores the enquiry even if optional email notification is not configured or fails.

## One-time activation

1. In GitHub repository Settings → Secrets and variables → Actions, add secrets:
   - `CLOUDFLARE_API_TOKEN` — scoped to the account with Workers Scripts edit and D1 read/edit/create permissions.
   - `CLOUDFLARE_ACCOUNT_ID`.
   - `TRADINGLAB03_ADMIN_API_KEY` — a long random secret used only for private submission retrieval.
   - `RESEND_API_KEY` (optional for storage; needed for email alerts).
2. Add repository variables:
   - `TRADINGLAB03_NOTIFY_EMAIL` — the inbox that should receive new enquiries.
   - `TRADINGLAB03_FROM_EMAIL` — a sender address verified by Resend, if email alerts are enabled.
   - `TRADINGLAB03_SITE_ORIGIN` — the exact website origin, e.g. `https://maazxhasan-hue.github.io` (origin only; no path).
3. Run **Deploy TradingLab03 Intake API** from GitHub Actions. It creates or reuses the D1 database, applies migrations, deploys the Worker, configures the owner key, and wires the deployed endpoint into the public website.
4. Check the workflow output and visit the `/health` URL. Submit a test enquiry with your own test email and confirm it appears in the owner notification or the protected admin endpoint.

If the Cloudflare credentials or owner key are missing, deployment intentionally fails instead of pretending the service is live. Without the optional Resend settings, submissions are still stored in D1 but no email alert is sent. The website only reports success after the API confirms the submission was saved.

## Owner-only retrieval

Use the deployed worker URL and owner key privately:

```sh
curl -H "Authorization: Bearer $TRADINGLAB03_ADMIN_API_KEY" \
  "https://YOUR-WORKER-URL/api/admin/submissions?limit=50"
```

Do not paste real client data into public issues, public workflow inputs, public artifacts, or committed files.
