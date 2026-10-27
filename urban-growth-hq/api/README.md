# Urban Growth HQ API

This is the dedicated API for Urban Growth HQ using its separate Cloudflare D1 database. The Worker is deployed at https://urban-growth-hq-api.maazxhasan.workers.dev and the database connection, lead persistence, duplicate detection, invalid-input rejection, and unauthorized-read rejection were verified on 2026-10-27. The n8n webhook integration is deploying separately and still requires an end-to-end verification after Render finishes deploying.

## Required setup

1. A separate Cloudflare D1 database named `urban-growth-hq-leads` has been provisioned (UUID `32c6ca74-1f50-4c22-b26d-197a6ef93ccb`). It is separate from the TradingLab03 intake database.
2. `wrangler.toml` is configured with the dedicated database UUID.
3. The schema is applied and verified against the live database.
4. The Worker is deployed and `GET /health` returns `database: connected`.
5. Set a strong random admin token as a Worker secret: `npx wrangler secret put ADMIN_TOKEN`.
6. Live tests: `GET /health` HTTP 200; valid `POST /api/leads` persisted; repeated email returned duplicate; invalid lead HTTP 400; unauthenticated `GET /api/leads` HTTP 401. A smoke-test lead is present in the dedicated database.

## Routes

- `GET /health`: checks database connectivity.
- `POST /api/leads`: validates and persists a lead, deduplicating by a SHA-256 contact key. It never sends outreach.
- `GET /api/leads`: returns a limited list only with `Authorization: Bearer <ADMIN_TOKEN>`.

## Security and limitations

- Keep the admin token secret; never put it in browser JavaScript or commit it to Git.
- This API intentionally does not send email, WhatsApp messages, or publish campaigns.
- Configure appropriate rate limiting / bot protection before public production use.
- The current static dashboard and n8n webhook are not automatically connected to this API. Update them only after deployment and successful live tests.
- Until these setup steps and tests pass, do not describe cloud persistence as active.
