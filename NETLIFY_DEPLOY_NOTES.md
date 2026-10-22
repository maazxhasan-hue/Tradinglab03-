# Hosting and deployment notes

Keep the private HQ site protected with team SSO. Deploy the public site separately and block private routes before making it public.

## Active hosting target (2026-10-22)

- Public website: Cloudflare Pages project `nexora-ai-public` at `https://nexora-ai-public.pages.dev`.
- Backup Pages project: `nexora-ai-public-2` at `https://nexora-ai-public-2.pages.dev`; retain while verifying the primary hostname.
- Legacy Pages project: `tradinglab03-legacy` at `https://tradinglab03.pages.dev`; retain as rollback until migration checks pass.
- Private HQ: `nexora-private-hq` on Netlify; keep team SSO enabled until a secure replacement is verified.
- Backend: TradingLab03 service on Render.
- Existing `tradinglab03-intake` Cloudflare Worker is production infrastructure; do not delete or modify it as part of the public-site migration.
- Vercel is retired and must not be treated as a deployment or release gate.

## Release verification

- Confirm the Cloudflare Pages production deployment is successful and the public URL serves the expected homepage.
- Verify public routes, navigation, redirects for private/admin paths, mobile layout, and forms.
- Verify API/backend connectivity against the Render service and the existing intake Worker without exposing secrets.
- Confirm the private HQ remains protected by team SSO.
- Keep Netlify available as rollback until the Cloudflare public site and all required integrations have been verified. Do not remove Netlify or the legacy Pages project before that sign-off.
