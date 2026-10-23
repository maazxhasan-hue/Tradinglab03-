# Private Nexora AI HQ

## Current runtime

The live Render service identified in this workspace is `nexora-hq-secure`, using `Dockerfile.private-hq` and `private_hq_server.py`. The authenticated owner workspace is served at the service root; login is `/login`, and the Growth HQ is `/growth-hq.html` after sign-in. The newer FastAPI workspace at `/hq` is a separate backend implementation and must not be assumed to be the live entry point for this service.

## Workforce execution

The authenticated Growth HQ supports two real AI execution paths:

- **Start 41 growth agents**: queues the canonical 41-role growth team.
- **Start full company workforce**: queues the roles in `company/roles.json` plus all 41 growth roles and processes them through the shared local Brain/task store.

These paths make actual model-provider requests. The work is internal and draft-only: they do not publish social posts, send DMs/emails, contact leads, spend money, place trades, or deploy production changes. A role definition is not proof of successful execution; check each batch's completed/failed counts and inspect saved task outputs.

## Required server configuration

Configure these as private Render environment variables, never in browser code or source control:

- `HQ_SESSION_SECRET`: random secret, at least 32 characters.
- `HQ_ACCESS_PASSWORD` **or** `HQ_ADMIN_PASSWORD`: unique owner password, at least 16 characters.
- One AI provider key: `OPENROUTER_API_KEY` (preferred; defaults to `openrouter/free`), `GEMINI_API_KEY`, or `OPENAI_API_KEY`.
- Optional model overrides: `OPENROUTER_MODEL`, `GEMINI_MODEL`, or `OPENAI_MODEL`.
- Optional remote shared Brain: `SHARED_BRAIN_AGENT_KEY` and `SHARED_BRAIN_AGENT_ID` (defaults to `company-agent-runtime`).

A free-tier model still requires a provider account/key. The application never fabricates a key. If no provider key is configured, the start action must fail closed and explain that configuration is missing.

## Persistence and restart behavior

The GrowthStore uses SQLite and creates its database directory automatically. Queued tasks can be resumed after a process restart when a provider key is configured. However, the currently identified Render service is on the free plan and has no persistent disk attached. SQLite data on its local filesystem can be lost when the container is replaced or redeployed. The remote Supabase shared Brain, when configured, stores shared memory but is not a substitute for durable task/queue storage. Do not describe the queue as fully durable across redeployments until a persistent disk or managed database is attached and verified.

## Deployment and verification

1. Review and merge the pull request only after relevant CI and security checks are green or remaining infrastructure-only failures are explicitly understood.
2. Render auto-deploys the `main` branch for `nexora-hq-secure`; wait for a successful live deployment of the intended commit.
3. Open the exact service URL shown in Render and sign in at `/login`.
4. Confirm the provider indicator shows a configured provider; confirm the Brain indicator shows local/remote readiness.
5. Start a small, bounded task first and verify the generated output and error reporting. Then start the full workforce only if the provider's quota/usage is acceptable.
6. Verify that failed tasks remain visibly failed and that successful tasks contain real outputs and evidence. Do not count queued work as completed work.
7. Check the authenticated APIs reject unsigned sessions and confirm no external side effect occurs from a draft-only task.

## Security boundaries

- Missing owner password/session secret causes startup to fail closed.
- The owner session is server-signed and uses Secure, HttpOnly, SameSite cookies.
- The HQ only exposes allowlisted documents and authenticated API routes.
- External publishing, outreach, purchases, trading, and production deployments remain approval-gated.
- Never commit provider credentials or put them in browser code, URLs, task outputs, or logs.

## Known live limitation

The code change and green CI do not prove that the live Render service has a provider key, remote Brain credentials, or durable storage. Verify these on the private Render service itself. This project should not be described as fully autonomous or error-free until real provider execution, persistence across redeployments, and live service behavior have been tested.
