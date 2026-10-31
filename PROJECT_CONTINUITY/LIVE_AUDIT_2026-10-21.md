# Live Audit — 2026-10-21

## What was checked
- Netlify site ID: 0386f7f4-90a0-4d15-a3b1-b730d4d32bc1
- Published deployment ID: 6ad87f7bcf17fc2d349c9c1b
- Published deployment state: `ready`
- Published deployment commit: `e6015a5e60947e6f6d2862a5332d150affd1f7ec`
- Published deployment title: `Fix city normalization in Harvey prospect discovery`
- Netlify environment-variable listing returned an empty list for the site.
- Deployment summary explicitly says: `No functions deployed`.
- Direct web verification of the public Mythos URL was unavailable in this audit; do not claim the page is live or working based only on source code.
- Supabase `mythos-generate` is ACTIVE, version 1, JWT verification enabled.
- Supabase database tables `mythos_projects`, `mythos_codex_entries`, `mythos_drafts` all have RLS enabled.
- Supabase security advisor returned no lints.
- Performance advisor reported five informational unused-index notices. These are not errors and do not justify dropping indexes while the feature is new.

## Blockers preventing honest completion
1. No site-level Netlify environment variables were returned. In particular, `OPENAI_API_KEY` is not present in the site-level list, so the Netlify AI fallback cannot be assumed configured.
2. The current published deployment has no Netlify Functions deployed, so the `/.netlify/functions/mythos` fallback is not available in that published deployment.
3. Supabase Edge Function source explicitly returns HTTP 503 when `OPENAI_API_KEY` is absent. The secret's presence in Supabase has not been verified and cannot be set with the available Supabase connector actions.
4. Existing Resend key values are not readable via the Resend connector; no domain was configured in the previous audit. Resend keys are unrelated to OpenAI generation and cannot be substituted.

## Required external step
The owner must privately add a valid OpenAI API key as `OPENAI_API_KEY` in Supabase Edge Function secrets at:
https://supabase.com/dashboard/project/ydstbryiwiigzlqbrcpo/settings/functions

Never paste the key into ChatGPT, commit it to GitHub, or expose it in frontend code. After adding it, test authenticated generation.

## Deployment steps still required
- Trigger a real Netlify production build from the intended current `main` branch (or use the connected Git provider's deploy workflow).
- Confirm that build publishes the current commit, includes `dashboard/mythos.html`, and deploys the `mythos` function from `netlify/functions/mythos.mts`.
- Confirm the published deployment's commit and functions list. Then test the public page and signed-out/signed-in generation.
- Test sign-up/sign-in, world creation, cloud draft save, and codex save with a real test account.
- Update `STATE.md` and `CHANGELOG.md` with actual deployment IDs and test results.

## Safety decision
No fake credentials were generated, no Resend keys were rotated/revoked, no secret was exposed, no protected HQ was changed, and no claim of live success is made.
