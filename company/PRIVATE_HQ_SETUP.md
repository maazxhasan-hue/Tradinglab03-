# Private Nexora AI HQ

## Purpose

The private HQ is served by the existing FastAPI backend at `/hq`; login is `/hq/login`; the protected read-only overview is `/hq/api/overview`. The dashboard displays persisted task/job counts, pending approvals, defined role count, recent status metadata, and integration configuration indicators. It does not expose task payloads, prospect details, approval content, or credentials. Defined roles do not prove agents are running.

## Render configuration

On the existing private Harvey backend service, configure `HQ_ADMIN_PASSWORD` as a long, unique secret and ensure `HQ_SESSION_SECRET` is a random secret of at least 32 bytes. The Render Blueprint declares the session secret as generated and the password as manually supplied. Preserve existing backend variables such as `HARVEY_API_KEY` and `DATABASE_PATH`. Never commit credentials or put them in browser code.

## Deploy

1. Merge the reviewed change into `main`.
2. Deploy the updated Dockerfile to the existing backend service; it starts `hq_app:app`.
3. Verify both HQ environment variables exist on that backend and restart/redeploy after changes.
4. Open the exact HTTPS hostname shown in Render followed by `/hq/login`. Do not guess the service hostname.
5. Update the static HQ transition page to link to that verified backend URL. A static site cannot enforce private authentication itself.

## Security

- Missing configuration fails closed with HTTP 503.
- The session cookie is signed server-side, HTTP-only, Secure, SameSite=Strict, scoped to `/hq`, and expires after eight hours.
- Login attempts are rate-limited after eight failures in a 15-minute window per keyed peer-address digest; the raw peer address is not stored.
- Unauthenticated `/hq` requests redirect to login; the overview API returns HTTP 401.
- Responses use no-store caching, nosniff, no-referrer, and frame-denial headers.
- The dashboard is read-only. It does not start agents, send messages, publish, spend money, approve work, deploy client projects, or collect payments.

## Required live checks

- [ ] CI tests pass.
- [ ] Backend health check passes after deployment.
- [ ] Signed-out page redirects and API returns 401.
- [ ] Wrong password issues no session; correct password issues Secure/HttpOnly/SameSite cookie.
- [ ] Authenticated overview returns only sanitized counts/status metadata.
- [ ] Logout and eight-hour expiry work.
- [ ] Verify mobile layout and actual deployed login flow.

## Status limitation

Code and green CI are not proof that the HQ is live. The Render workspace/service must be selected, environment variables configured on the correct backend, changes merged/deployed, and hosted behavior verified. This document does not claim those external steps have happened.

## Pricing Management

The private owner workspace includes a separate page at `/hq/pricing`. It manages service packages, AI-agent subscriptions, and client-specific quotes through the authenticated backend.

- `GET /hq/api/pricing`: owner-only list; supports `include_archived=true`.
- `POST /hq/api/pricing`: create a draft.
- `PUT /hq/api/pricing/{id}`: save draft changes. Editing a published record does not change the live snapshot.
- `POST /hq/api/pricing/{id}/publish`: validate and publish the saved snapshot.
- `POST /hq/api/pricing/{id}/archive`: archive an item and remove it from the public catalog.
- `GET /hq/api/pricing/{id}/history`: owner-only audit history.
- `GET /public/pricing`: public, read-only catalog containing only published service/subscription snapshots. Drafts, audit logs, and client-specific quotes are never exposed.

Amounts are stored as integer paise. The API rejects malformed slugs, unsupported categories/billing periods, negative amounts, amounts with more than two decimal places, invalid discounts, duplicate slugs, and promotional prices that are not below the regular price. Create, update, publish, and archive actions are persisted to `pricing_audit_log`.

Client-specific quotes can be finalized as owner-only records, but this feature does not email or share a quote with a customer, create invoices, take payments, or update an external website automatically. The public website must consume `/public/pricing` separately if customer-facing price cards are desired.

## Pricing deployment checks

- [ ] Pricing tables persist on the configured backend database.
- [ ] Unauthenticated requests cannot read or change the owner catalog.
- [ ] A saved draft is absent from `/public/pricing`.
- [ ] Publishing a service/subscription exposes only the published snapshot.
- [ ] Editing a published item leaves its previous public snapshot active until republished.
- [ ] Client-specific quotes never appear in the public catalog.
- [ ] Invalid prices and duplicate slugs are rejected.
- [ ] Audit history records create/edit/publish/archive events.
- [ ] Archive removes a price from the public catalog.
- [ ] Backend CI passes and the deployed HTTPS HQ page is verified manually.
