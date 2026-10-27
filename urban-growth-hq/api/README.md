# Urban Growth HQ API

This is the dedicated API intended to persist leads in a separate Cloudflare D1 database. It is **not live until a new D1 database is provisioned, the schema is applied, the Worker is deployed, and the API is tested**.

## Required setup

1. Create a separate Cloudflare D1 database named `urban-growth-hq-leads` (do not reuse the TradingLab03 or any other database).
2. Update `wrangler.toml` with the new database UUID.
3. Apply `schema.sql` with Wrangler: `npx wrangler d1 execute urban-growth-hq-leads --remote --file=./schema.sql`.
4. Deploy from this directory: `npx wrangler deploy`.
5. Set a strong random admin token as a Worker secret: `npx wrangler secret put ADMIN_TOKEN`.
6. Test `GET /health`, valid/invalid `POST /api/leads`, duplicate submission, and authorized/unauthorized `GET /api/leads`.

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
