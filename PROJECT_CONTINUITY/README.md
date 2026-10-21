# Nexora AI / TradingLab03 — Permanent Project Continuity

This folder is the durable handoff record for work on this project. It is stored in GitHub, not only in a ChatGPT conversation, so it remains available if a conversation is deleted or reaches its context limit.

## Master index
Start with [MASTER_PROJECT_INDEX.md](MASTER_PROJECT_INDEX.md) for the current project map, referral and backup work, integration requests, verification status, and next actions.
## Source of truth
- Repository: https://github.com/maazxhasan-hue/Tradinglab03-
- Main branch: `main`
- Public website currently associated with this project: https://nexora-ai-public.netlify.app/
- Mythos page intended URL: https://nexora-ai-public.netlify.app/dashboard/mythos.html
- Supabase project: `ydstbryiwiigzlqbrcpo`

## Rules for future work
1. Read `PROJECT_CONTINUITY/STATE.md` before making project changes.
2. Treat the existing repository and deployed services as the project source of truth. Do not blindly replace files, remove existing functionality, rename services, or overwrite unrelated project folders.
3. Make actual code/configuration changes in their proper application folders. Do not put application source code in this continuity folder unless it is documentation or a safe recovery copy.
4. After every meaningful task, update `STATE.md` and append a dated entry to `CHANGELOG.md` with what changed, commit/deployment IDs where available, verification performed, remaining blockers, and the exact next step.
5. Never claim something is deployed, working, or verified unless it was actually checked.
6. Never commit API keys, passwords, access tokens, service-role keys, private credentials, or secret values. Record only secret *names* and their setup status.
7. Keep existing project history and commits; prefer small, reviewable changes.
8. If work continues in a new ChatGPT conversation, use this folder and the repository history to resume from the recorded checkpoint.

## Important limitation
This folder is a persistent continuity/checkpoint folder, not a second byte-for-byte copy of every repository file or external cloud service. The Git repository's tracked files and commit history are the durable copy of source code. Supabase/Netlify/Resend settings and secret values are not automatically backed up here. Never store secrets in this repository.
