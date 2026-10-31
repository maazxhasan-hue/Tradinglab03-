# Urban Growth HQ API — Live verification (2026-10-27)

## Live deployment
- Worker: `urban-growth-hq-api`
- Base URL: `https://urban-growth-hq-api.maazxhasan.workers.dev`
- Health endpoint: `GET /health`
- Lead intake endpoint: `POST /api/leads`
- Lead list endpoint: `GET /api/leads` (requires `ADMIN_TOKEN` secret)
- Dedicated D1 database: `urban-growth-hq-leads`
- Database UUID: `32c6ca74-1f50-4c22-b26d-197a6ef93ccb`

## Tests run
- Health returned HTTP 200 and `database: connected`.
- Valid synthetic lead returned HTTP 200 and `storage_status: persisted`.
- Invalid lead returned HTTP 400.
- Repeating the same synthetic contact returned `status: duplicate` with the original lead ID.
- Synthetic lead used `contactConsent: false`, so `contact_allowed` remained false.

## Still not complete
- The static Urban Growth dashboard and the n8n lead webhook are not yet wired to this API. Existing dashboard entries remain browser-local until that integration is implemented.
- The admin token secret must be configured before authenticated lead-list access can work.
- No email/WhatsApp/call follow-up or social publishing is connected. Do not claim these are active.
- Before production launch, connect the dashboard form to this API, add authenticated admin access for viewing/updating leads, configure rate limiting/bot protection, and run end-to-end tests through the public dashboard.
