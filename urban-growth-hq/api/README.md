# Urban Growth HQ API

Dedicated Cloudflare Worker + D1 lead service for Urban Growth HQ.

- Worker: https://urban-growth-hq-api.maazxhasan.workers.dev
- Database: `urban-growth-hq-leads` (dedicated D1 database)
- Dashboard: https://urban-growth-hq.onrender.com
- Lead intake webhook: https://urban-growth-n8n.onrender.com/webhook/urban-growth-hq-lead-intake

## Routes
- `GET /health` checks D1 connectivity.
- `POST /api/leads` validates and persists leads, deduplicating by a SHA-256 contact key. No messages are sent.
- `GET /api/leads?limit=50` requires `Authorization: Bearer <ADMIN_TOKEN>`.
- `PATCH /api/leads` requires the same token and updates an allowed lead status.

## Security and operation
- `ADMIN_TOKEN` is configured as a Cloudflare Worker secret. Never commit it or put it in browser source.
- The dashboard asks for the token only when connecting cloud leads; it keeps the token in page memory for that session, not localStorage.
- CORS permits the Urban Growth HQ dashboard origin and the required GET/POST/PATCH methods.
- The n8n webhook is configured for the dashboard origin. It validates, persists to D1 through the Worker, rejects invalid input and deduplicates repeat submissions.
- Consent is recorded separately; no outreach, publishing, purchasing, or trading is triggered.
- Campaigns, showings, calls, tasks and knowledge notes remain browser-local. Export backups regularly.
- The 41 specialist roles are definitions, not 41 continuously executing agents. AI provider execution is not enabled by this API.

## Smoke checks
```sh
curl -i https://urban-growth-hq-api.maazxhasan.workers.dev/health
curl -i -X POST https://urban-growth-n8n.onrender.com/webhook/urban-growth-hq-lead-intake -H 'Content-Type: application/json' -d '{"name":"Example","email":"example@example.com","contactConsent":false}'
curl -i https://urban-growth-hq-api.maazxhasan.workers.dev/api/leads
```
The final command should return HTTP 401 without an admin token. Do not use real customer details in smoke tests.
