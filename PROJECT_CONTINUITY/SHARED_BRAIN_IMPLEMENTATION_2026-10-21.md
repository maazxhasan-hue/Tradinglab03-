# Shared Brain Implementation Checkpoint — 2026-10-21

## Completed
- Added Supabase migration `agent_shared_brain_memory`.
- Created `public.agent_shared_memory` with user/project/namespace scope, JSONB content, summary, tags, source agent, confidence, provenance, version, timestamps, and optional expiry.
- Enabled RLS; authenticated access is restricted to rows whose `user_id = auth.uid()`; anon has no table privileges.
- Added scoped recency and tags indexes.
- Deployed Edge Function `shared-brain`, ID `683fba19-d8aa-490f-8a61-0a08348da0db`, version 1, ACTIVE, JWT verification enabled.
- Function validates the access token via Supabase Auth and uses the caller's JWT for database operations. Actions: `recall`, `remember`. It does not accept caller-supplied user IDs.
- API docs: `docs/SHARED_BRAIN_API.md`.

## Endpoint
`POST https://ydstbryiwiigzlqbrcpo.supabase.co/functions/v1/shared-brain`

## Not yet complete
- No agent integrations have yet been proven. Existing workflows/services need inventory and per-runtime auth design.
- No authenticated end-to-end request was executed because no user session token was available in this run.
- The recall/remember API is not a generative model; it is shared persistent context.
- Conflict behavior needs a concurrency-safe version strategy before heavy multi-agent writes. Current upsert version increment can race if two agents update the same key simultaneously.
- Expiry input should be validated more strictly before production use.
- Do not say all agents use one brain until each intended agent is integrated and cross-agent tests pass.

## Safety
- Keep service-role keys and model-provider keys out of the client and shared memory.
- Do not disable JWT verification for convenience.
- Keep existing private HQ untouched.


## Follow-up work — 2026-10-21 (continued)
- Added `tests/test_shared_brain_client.py` (commit `29b66029f1362b504abd8d3eb9ec44041d02a6c1`) covering unconfigured-client rejection, machine/user auth headers, bounded recall/query inputs, malformed responses, and redacted HTTP errors. These tests have been committed but have NOT yet been executed in a local or CI test run.
- The machine-auth service key is shared across machine callers; `x-agent-id` is a caller-supplied label, not cryptographic per-agent identity. Treat it as a shared trusted-service credential, restrict who can access it, and do not treat the label as a strong authorization boundary.
- The registry workflow's configured list of workflow names remains unverified against all actual workflow `name:` fields. A registry entry is telemetry, not proof that the workflow's agent consumes shared context.
- Current status remains PARTIAL: machine key not configured in this session, no live authenticated read/write or cross-agent recall test, and Harvey's runtime has not been proven integrated. Do not redesign HQ until those checks pass.
