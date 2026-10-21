# Current Project State — Nexora AI / TradingLab03

Last checkpoint: 2026-10-21  
Primary repository: https://github.com/maazxhasan-hue/Tradinglab03-  
Branch: `main`

## Current objective
Continue completing the Nexora AI project and Mythos module safely, preserve the existing website and protected HQ, and make all future work resumable from this folder.

## Project services
- GitHub repository: `maazxhasan-hue/Tradinglab03-`
- Public Netlify site: https://nexora-ai-public.netlify.app/
- Netlify site ID: `0386f7f4-90a0-4d15-a3b1-b730d4d32bc1`
- Supabase project ref: `ydstbryiwiigzlqbrcpo`
- Supabase URL: https://ydstbryiwiigzlqbrcpo.supabase.co
- Supabase dashboard: https://supabase.com/dashboard/project/ydstbryiwiigzlqbrcpo
- Supabase Edge Function secrets page: https://supabase.com/dashboard/project/ydstbryiwiigzlqbrcpo/settings/functions
- Private Render HQ service: `nexora-internal-hq` (SSO-protected; do not modify without explicit project-specific need)
- Keep current Netlify site name; do not rename it.

## Mythos implementation already committed
Relevant files:
- `dashboard/mythos.html`
- `netlify/functions/mythos.mts`
- `netlify.toml`

Relevant commits on main:
- `9817ca63127776dbf4890edc897d811fe1b96a01` — initial Mythos dashboard
- `cca411ba4bf38a6c79c9991281290f618aae6975` — Netlify function
- `3b3a1db7dcf077734d2024cd228b527f5a48a858` — Supabase auth/workspace UI
- `0b499ac745cfe312461f3e6d910f2a4f15a5756e` — initial signed-in generation routing
- `617110d86a33f916b06ed34e4cb25f74141fcf18` — signed-in generation routed to Supabase Edge Function

Source links:
- https://github.com/maazxhasan-hue/Tradinglab03-/blob/main/dashboard/mythos.html
- https://github.com/maazxhasan-hue/Tradinglab03-/blob/main/netlify/functions/mythos.mts
- https://github.com/maazxhasan-hue/Tradinglab03-/blob/main/netlify.toml

Mythos features in the dashboard include mode/genre/POV/TTRPG controls, prompt and command chips, output/copy/download, Supabase email sign-up/sign-in/sign-out, project creation, cloud draft saving, and lore codex saving.

## Supabase database
Migrations already applied:
1. `mythos_workspace_schema`: `public.mythos_projects`, `public.mythos_codex_entries`, `public.mythos_drafts`, RLS enabled and user/project ownership policies applied; authenticated-only grants.
2. `mythos_security_and_index_fixes`: indexes added to user_id fields; public/anon/authenticated execute revoked on existing `public.rls_auto_enable()` security-definer function.

The latest recorded table check showed RLS enabled on all three tables. The security advisor returned no lints at the last check.

## Supabase Edge Function
- Function: `mythos-generate`
- Function ID: `a6e0cfe2-dd5a-46cf-97b0-36bc2ac3a312`
- Last known status: ACTIVE, version 1, JWT verification enabled.
- Uses OpenAI Chat Completions model `gpt-4o-mini`.
- Reads `OPENAI_API_KEY` server-side from the function environment.
- If that secret is absent, generation returns HTTP 503.
- **Blocker:** presence of `OPENAI_API_KEY` in Supabase secrets has not been verified. The connector tools available during the last session could not set Edge Function secrets. Add it privately through the Supabase secrets dashboard, never in chat, frontend code, or Git.
- After adding the secret, test generation with an authenticated user and inspect errors before declaring the feature complete.

## Resend API keys
The connected Resend account exposed key metadata only:
- `Nexora-AI-Test` — ID `97d1240f-93d2-4d69-9916-0407f2a99961`
- `Nexora AI Website` — ID `08b8c50f-061c-48b5-b586-3ec3efba2568`

The original secret values are not readable through the connected Resend tool, so they cannot be copied automatically into Supabase. Resend API keys are for Resend email APIs; they do not substitute for an OpenAI API key. No Resend domains were found in the last check. No email-sending feature was confirmed implemented. Only add `RESEND_API_KEY` server-side if/when an email feature is built. Do not rotate or revoke keys without explicit approval.

## Deployment verification status
- Latest known `netlify.toml` SHA recorded previously: `da90d2e25a67351403be7d8992c07a877f7c8f48`.
- At the last recorded check, the live Netlify deployment was still reported as previous deployment `6ad87f7bcf17fc2d349c9c1b`, state `ready`; deployment of latest Mythos changes had **not** been verified.
- Do not say Mythos is live/fully working until the current deployment is checked at https://nexora-ai-public.netlify.app/dashboard/mythos.html and an end-to-end test passes.

## Secrets and safety
- Never store secret values in this repository or continuity folder.
- Supabase publishable key is intended for client use; do not expose Supabase service-role/secret keys.
- Never ask the user to paste API keys into chat. Direct them to the provider's private secrets UI.
- Do not alter the private HQ, protected directories, or unrelated trading systems while fixing Mythos unless explicitly requested.

## Exact next steps
1. Inspect the current `main` branch and latest deployment status before editing anything.
2. Verify the Mythos page and Netlify function configuration in the live deployment.
3. Have the user add `OPENAI_API_KEY` privately in Supabase Edge Function secrets; then test the deployed `mythos-generate` function using a signed-in session.
4. Fix any build/runtime errors found, preserving unrelated site features.
5. Verify project creation, draft saving, and codex saving under authenticated RLS.
6. Update this file and `CHANGELOG.md` after every meaningful change with exact commit/deployment references and test results.

## Scope note
This checkpoint documents the latest known project state from prior work; external cloud state can change independently. Always re-check before assuming it remains current.
