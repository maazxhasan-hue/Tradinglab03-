# Nexora hosting and deployment notes

Keep the private HQ site protected with team SSO. Deploy the public site separately and block private routes before making it public.

## Active hosting target (2026-10-22)

- Public website: Cloudflare Pages project `nexora-ai-public` at `https://nexora-ai-public.pages.dev`.
- Backup Pages project: `nexora-ai-public-2` at `https://nexora-ai-public-2.pages.dev`; retain while verifying the primary hostname.
- Legacy Pages project: `tradinglab03-legacy` at `https://tradinglab03.pages.dev`; retain as rollback until migration checks pass.
- Private HQ: `https://nexora-internal-hq.onrender.com` on Render; keep authentication and private-route protections enabled.
- Backend: TradingLab03 service on Render.
- Existing `tradinglab03-intake` Cloudflare Worker is production infrastructure; do not delete or modify it as part of the public-site migration.
- Vercel is retired and must not be treated as a deployment or release gate.

## Release verification

- Confirm the Cloudflare Pages production deployment is successful and the public URL serves the expected homepage.
- Verify public routes, navigation, redirects for private/admin paths, mobile layout, and forms.
- Verify API/backend connectivity against the Render service and the existing intake Worker without exposing secrets.
- Confirm the private HQ remains protected by team SSO.
- Netlify and Vercel are retired deployment targets and must not be used for releases or rollback. Do not delete legacy hosting projects or credentials without a separate inventory and owner-approved cleanup.
