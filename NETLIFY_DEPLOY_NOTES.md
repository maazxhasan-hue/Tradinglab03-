# Netlify deployment notes

Keep the private HQ site protected with team SSO. Deploy the public site separately and block private routes before making it public.

## Active hosting target (2026-10-22)

- Public website: `nexora-ai-public` on Netlify.
- Private HQ: `nexora-private-hq` on Netlify; keep team SSO enabled.
- Backend: TradingLab03 service on Render.
- Vercel is retired and must not be treated as a deployment or release gate.
- After merging to `main`, verify each Netlify site's published production deploy points to the intended current commit. A successful GitHub preview or Render deploy does not prove the Netlify production site was updated.
