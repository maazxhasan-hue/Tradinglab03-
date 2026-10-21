# Project Work Log

## 2026-10-21 — Continuity checkpoint created
- Added this permanent GitHub-hosted continuity folder so project work can resume after a chat is deleted or reaches its context limit.
- Recorded known repository/service references, Mythos commits and files, Supabase schema/function status, Resend key metadata limitations, deployment uncertainty, security constraints, and exact next steps.
- No credentials or secret values were included.
- Verification note: this entry is a written checkpoint based on the latest recorded work. It does not itself verify the current live deployment or cloud secret configuration.
- Next action: inspect current repository/deployment state and continue from the steps in `STATE.md`.

## 2026-10-21 — Live deployment audit
- Inspected the published Netlify deployment: `6ad87f7bcf17fc2d349c9c1b`, commit `e6015a5e60947e6f6d2862a5332d150affd1f7ec`, state `ready`.
- Netlify site-level environment-variable listing was empty; deployment summary says no functions deployed. Mythos live deployment and AI generation are therefore not verified and remain blocked.
- Rechecked Supabase: `mythos-generate` active with JWT verification enabled; all three Mythos tables have RLS enabled; security advisor has no lints.
- Added `PROJECT_CONTINUITY/LIVE_AUDIT_2026-10-21.md` with the evidence and required steps.
- Remaining owner-only requirement: add `OPENAI_API_KEY` privately in Supabase Edge Function secrets. Then trigger a Netlify production build that includes the current source and functions, and perform authenticated end-to-end tests.
- No secrets were added to GitHub; no credentials were rotated or revoked; private HQ remains untouched.

## 2026-10-21 — Session log saved
- Created `PROJECT_CONTINUITY/SESSION_LOG_2026-10-21.md` with the current audit findings, verified IDs/statuses, blockers, safe secret-handling rules, and exact resume tasks.
- Commit: `f559c8f135432fcbdb28a892ba6a2e28346973ce`.
- The file is a durable work log, not a verbatim copy of every chat message. Future meaningful work should be appended to the changelog and reflected in STATE.md.

## 2026-10-21 — Shared brain requirement
- Added `PROJECT_CONTINUITY/SHARED_BRAIN_ARCHITECTURE.md` to specify that all Nexora agents should share a common brain through a central API and persistent store, with agent identity, access isolation, provenance, versioning, and audit logging.
- Updated `STATE.md` to include this requirement and the implementation plan.
- Commits: architecture `eb8d3889965c4fa5d9be291a7da85839de12cce4`; state `9b1763f430332ce255ec682177deff9ada9add2a`.
- Status is requirement documented only. Agent inventory, shared API/store implementation, integrations, and cross-agent tests are still pending.

## 2026-10-21 — Shared Brain v1 deployed
- Applied Supabase migration `agent_shared_brain_memory` to project `ydstbryiwiigzlqbrcpo`, creating user-scoped memory records with RLS, project/namespace scope, provenance, confidence, versioning, expiry, and indexes.
- Deployed Edge Function `shared-brain` (ID `683fba19-d8aa-490f-8a61-0a08348da0db`, version 1, ACTIVE, JWT verification enabled). Supports authenticated `recall` and `remember`; validates caller through Supabase Auth and uses caller JWT for RLS-scoped database access.
- Added API contract at `docs/SHARED_BRAIN_API.md` (commit `75c1aadd9420f88669ed1fd27f07fb6c481f1a44`) and implementation checkpoint at `PROJECT_CONTINUITY/SHARED_BRAIN_IMPLEMENTATION_2026-10-21.md` (commit `4f3c3e7ff06cf75585ebd520a81844b1805e0370`).
- Migration tool returned success. Edge deployment returned ACTIVE. Authenticated end-to-end read/write and cross-agent integration are NOT yet verified; do not claim every agent is connected.
- Known follow-ups: test with real signed-in user session, improve concurrent version increments/expiry validation, inventory each agent runtime, design separate server-to-server identity where needed, then integrate and run cross-agent isolation tests.

- Added `company/shared_brain.py` (commit `2e04e0dd34362ceb7c82e9df89109512d52d273e`), an authenticated Python client exposing `recall` and `remember` with bounded requests, timeouts, and redacted errors. It is a reusable integration adapter; existing Python/Harvey/GitHub workflow agents have not yet been wired to it or tested with real credentials.

- Integrated optional shared-brain recall/write into `company/agent_runtime.py` (commit `b9b6f085e6ca79dba2f63e1fe717c771f42fb13d`). When a valid Supabase user access token and publishable key are supplied via environment variables, this runtime recalls scoped company memories before drafting and writes a task-result metadata record after completion. If shared brain is unavailable, task processing continues and reports the status. Not yet run through repository tests or verified with live credentials; the other agent families remain to be integrated.

## 2026-10-21 — Broader Shared Brain integration
- Added service-to-service memory store `public.agent_shared_facts` with RLS enabled and direct anon/authenticated access revoked via migration `agent_shared_facts_service_store` (Supabase tool reported success).
- Updated Supabase Edge Function `shared-brain` to version 2 (ID `683fba19-d8aa-490f-8a61-0a08348da0db`, ACTIVE). It now supports either a validated user JWT (user-isolated `agent_shared_memory`) or a machine request using `x-agent-key` / `x-agent-id` (shared `agent_shared_facts`). Function JWT verification is set false because it performs explicit request authentication itself; unauthenticated requests are rejected by function code. Machine auth requires `SHARED_BRAIN_AGENT_KEY` and server-side Supabase service-role environment configuration.
- Updated `company/shared_brain.py` to support machine-agent credentials (commit `f857df638e2e0353ce2af1b0acadf4a4b5888553`).
- Added `company/shared_brain_sync.py` (commit `a13f736e0c72828de7982a79433b0fc8733688af`) to publish sanitized workflow run metadata only.
- Added shared-brain sync steps to the AI Draft Worker, Autonomous Client Execution, Daily Company Operations, and Hourly Opportunity Scout workflows. Commits: `f086cebd4781122ec6f6b55c920a3c4c558c468d`, `2eb63ac2e357012445eb43aee5de95202548f638`, `04226d4c2a5f03b9304d0466b4e37c049e6a163a`, `47d0f001283c97070d8142af978368aa632cfb25`.
- Added `.github/workflows/shared-brain-registry.yml` (commit `f8135b72002d4b3febdfaff6c15085234294fe60`) to register completed runs from major workflow families. Added machine-auth setup instructions in `docs/SHARED_BRAIN_API.md` (commit `77652c8461262320727822b62ce143f1edda2649`).
- Python company runtime and bounded tool agent can recall/save memory when machine credentials are configured; company runtime integration commit `b9b6f085e6ca79dba2f63e1fe717c771f42fb13d`, tool-agent integration commit `f24f184c81ca2e9109400d567d781be077086603`.
- BLOCKER: `SHARED_BRAIN_AGENT_KEY` must be set privately in both Supabase Edge Function secrets and GitHub Actions repository secrets before unattended integrations can write. This secret has not been configured or tested in this session. No authenticated end-to-end cross-agent test has passed yet. Other direct service runtimes (including Harvey API internals) are not yet proven to consume shared memories. HQ theme redesign intentionally not started until shared brain work is verified.
