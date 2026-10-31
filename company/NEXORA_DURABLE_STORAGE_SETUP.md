# Nexora durable storage setup

The HQ's task history and pricing stores support SQLite for local tests and PostgreSQL for production. Both stores use `DATABASE_URL` automatically when it is set to a PostgreSQL connection string.

## Required production configuration

1. Provision a non-expiring managed PostgreSQL database (or upgrade the existing database before its free expiry).
2. Attach its private connection string to the private HQ service as the secret environment variable `DATABASE_URL`. Do not put the URL in source control or chat.
3. Ensure the database's network policy allows connections from the HQ service in the same Render workspace/region.
4. Deploy the HQ after the environment variable is present.
5. Verify the authenticated task and pricing endpoints, create a test task, update a test price, restart/redeploy the service, and confirm both values survive.
6. Before switching a live instance, take a backup and migrate any existing SQLite rows. Do not simply point the service at an empty database and assume old records were copied.

The schema bootstrap creates the approval table before task tables when PostgreSQL is selected. Existing SQLite tests remain the default when `DATABASE_URL` is absent.

## Sensitive actions

Social publishing, outbound messages, purchases, price changes, and other external actions must stay disabled until a real platform connector is configured and the server-side approval record is checked. A provider API key or a successful draft-generation test alone does not authorize external side effects.

## Verification checklist

- [ ] `DATABASE_URL` is configured in Render without exposing its value.
- [ ] PostgreSQL-backed schema bootstrap passes.
- [ ] Task create/read/status transitions pass against PostgreSQL.
- [ ] Pricing update persists and still enforces the ₹499 cap.
- [ ] Restart/redeploy persistence test passes.
- [ ] Live platform credentials and scopes are verified separately for each external connector.
- [ ] Publishing/messaging/purchase actions remain blocked until explicit approval.
