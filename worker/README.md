# TradingLab03 enquiry service

This Cloudflare Worker is the Nexora AI public enquiry intake service (the repository retains the legacy TradingLab03 name). It does not connect to trading, brokerage, MCX, or Azure trading infrastructure.

## What it does

- Requires a client account for project submissions. `POST /api/auth/register` and `/api/auth/login` issue a random bearer session token after password verification; `GET /api/auth/me` validates the session and `POST /api/auth/logout` revokes it. Passwords are PBKDF2-SHA-256 hashed with per-account random salts; session tokens are hashed before D1 storage and expire after seven days.
- Receives authenticated website project enquiries at `POST /api/intake` and saves them to Cloudflare D1, associated with the signed-in account.
- Validates input, enforces a strict allowed-origin check, caps request size, uses a honeypot, rate-limits enquiry submission and authentication attempts by a one-way IP hash, and rejects anonymous project submissions.
- Sends an email notification through Resend only when all three settings are configured: `RESEND_API_KEY`, `NOTIFY_EMAIL`, and `FROM_EMAIL`. The sender address must be verified with Resend.
- Exposes `GET /health` for a non-sensitive health check.
- Exposes `GET /api/admin/submissions` only with an `Authorization: Bearer ...` owner key; supports owner-authenticated `PATCH /api/admin/submissions/{id}/status` to set a validated pipeline status (`new`, `reviewing`, `qualified`, `proposal_ready`, `in_progress`, `delivered`, `won`, `lost`); and supports owner-authenticated `DELETE /api/admin/submissions/{id}` for deletion requests. The owner key must never be placed in the public website. A `won` label is an operator-entered sales status, not payment evidence.
- Stores the enquiry even if optional email notification is not configured or fails.

## One-time activation

1. In GitHub repository Settings → Secrets and variables → Actions, add secrets:
   - `CLOUDFLARE_API_TOKEN` — scoped to the account with Workers Scripts edit and D1 read/edit/create permissions.
   - `CLOUDFLARE_ACCOUNT_ID`.
   - `TRADINGLAB03_ADMIN_API_KEY` — a long random secret used only for private submission retrieval.
   - `RESEND_API_KEY` (optional for storage; needed for email alerts).
2. Add repository variables:
   - `TRADINGLAB03_NOTIFY_EMAIL` — the inbox that should receive new enquiries.
   - `TRADINGLAB03_FROM_EMAIL` — a sender address verified by Resend for production. For a no-domain test only, leave this variable unset; deployment uses Resend's `onboarding@resend.dev` test sender by default. Resend test mode is limited and may only deliver to the email address associated with your Resend account. For real client notifications, verify a domain you control and set this variable to that domain's sender address.
   - `TRADINGLAB03_SITE_ORIGINS` — comma-separated exact website origins (no paths), e.g. `https://nexora-ai-sooty-two.vercel.app,https://maazxhasan-hue.github.io`. Keep this list limited to domains you control; the deploy workflow uses the Vercel site and GitHub Pages as defaults if this variable is unset.
3. Run **Deploy TradingLab03 Intake API** from GitHub Actions. It creates or reuses the D1 database, applies migrations, deploys the Worker, configures the owner key, and wires the deployed endpoint into the public website.
4. Check the workflow output and visit the `/health` URL. Submit a test enquiry with your own test email and confirm it appears in the owner notification or the protected admin endpoint.

If the Cloudflare credentials or owner key are missing, deployment intentionally fails instead of pretending the service is live. Without `RESEND_API_KEY` or `TRADINGLAB03_NOTIFY_EMAIL`, submissions are still stored in D1 but no email alert is sent. The default `onboarding@resend.dev` sender is for testing only; it does not remove Resend's recipient restrictions or replace domain verification for production. The website only reports success after the API confirms the submission was saved.

## Owner inbox and private retrieval

After deployment, open the owner inbox at `https://nexora-ai-sooty-two.vercel.app/dashboard/inbox.html` (or the matching `/dashboard/inbox.html` path on your configured site) on a trusted device and enter the owner key. The inbox page keeps the key in the current page only, lists private enquiries, offers a manual email-reply link, and confirms before deleting a record. The key is never embedded in the public HTML.

For command-line retrieval, use the deployed worker URL and owner key privately:

```sh
curl -H "Authorization: Bearer $TRADINGLAB03_ADMIN_API_KEY" \
  "https://YOUR-WORKER-URL/api/admin/submissions?limit=50"
```

Delete a single submission privately with `curl -X DELETE -H "Authorization: Bearer $TRADINGLAB03_ADMIN_API_KEY" "https://YOUR-WORKER-URL/api/admin/submissions/SUBMISSION-UUID"`. Treat the owner key and returned customer details as confidential.

Do not paste real client data into public issues, public workflow inputs, public artifacts, or committed files.


## Lead pipeline status updates

The private inbox uses the status endpoint with the owner bearer key:

```http
PATCH /api/admin/submissions/{submission-id}/status
Authorization: Bearer YOUR_OWNER_KEY
Content-Type: application/json

{"status":"qualified"}
```

Only the eight documented status values are accepted. The endpoint rejects unauthenticated requests, validates the UUID, limits the request body, and returns whether a matching record was updated. Do not store the owner key in browser storage, source control, or a public URL.

The status field is operational bookkeeping only. A lead marked `won` is not proof of a signed contract, invoice, payment, or revenue. Payment reconciliation remains a separate, unimplemented production integration.


## Client sign-in

The public website links to `dashboard/login.html`. New clients can register with a valid email and a unique password of at least 12 characters, then return to the project brief. The browser stores the short-lived bearer token in local storage; the Worker validates it server-side on every project submission. Tokens expire after seven days, and logout revokes the current session. Authentication attempts are rate-limited. The current account flow does not yet verify email ownership or provide password-reset/recovery; do not describe it as email-verified identity. Keep the Worker endpoint and account data private, and add verified email recovery before relying on accounts for sensitive client documents.
