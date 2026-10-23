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