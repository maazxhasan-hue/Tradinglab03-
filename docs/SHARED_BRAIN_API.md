# Nexora Shared Brain API

Status: **v1 deployed; not yet integrated into every agent.**

## Endpoint
`POST https://ydstbryiwiigzlqbrcpo.supabase.co/functions/v1/shared-brain`

Requires a valid Supabase Auth access token:
`Authorization: Bearer <user_access_token>`
`apikey: <Supabase publishable key>`
`Content-Type: application/json`

Never place service-role keys, provider API keys, or other secrets in browser code or shared memory.

## Recall
```json
{"action":"recall","project_key":"nexora","namespace":"general","limit":20}
```
Optional `query` filters summaries. Maximum 50 records.

## Remember
```json
{"action":"remember","project_key":"nexora","namespace":"general","memory_key":"decision:shared-brain","source_agent":"mythos","summary":"Shared brain API is available","content":{"status":"deployed"},"tags":["architecture"],"confidence":0.9,"source_ref":"commit-or-task-reference"}
```
Each key is unique per user/project/namespace. Existing keys are updated and versioned. Content limit is 20 KB; summary limit 2,000 characters. Use provenance and confidence; store verified facts, not credentials.

## Isolation and limitations
- The API validates the bearer token against Supabase Auth and uses the caller's JWT for database requests.
- Database RLS scopes rows to the authenticated user's `auth.uid()`; the client cannot choose another user ID.
- The current implementation supports recall and remember only; no public delete endpoint.
- Memory is scoped by `project_key` and `namespace`. Keep projects separated.
- This endpoint is a shared memory primitive, not a model/LLM by itself.
- Agents using GitHub Actions or other runtimes still need an approved user session or a separately designed server-to-server identity. Do not share a user's bearer token among agents or disable JWT verification to make integration easier.
- Existing agents have not all been connected. Integrate each one deliberately and test cross-agent recall, RLS isolation, conflict behavior, and stale/unavailable memory.
- Never store secrets, raw credentials, or sensitive personal data in shared memory.


## Unattended agent/workflow authentication
The Edge Function also supports machine-to-machine requests for unattended agents:
- `x-agent-key: <shared machine secret>`
- `x-agent-id: <stable agent identifier>`
- JSON body uses the same `recall` / `remember` actions.

Machine requests use the separate `public.agent_shared_facts` store, shared across connected agents within a project/namespace. User-session requests continue to use `public.agent_shared_memory` and are isolated per user. The service table denies direct anon/authenticated table access; the Edge Function uses the server-side service-role credential only after the machine secret matches. Never send the service-role key to a client or workflow.

### GitHub Actions workflow registry via OIDC

The workflow registry uses a short-lived GitHub Actions OIDC token instead of a long-lived repository secret:
- The workflow requests audience `nexora-shared-brain` and sends the token in `x-github-oidc-token` with `x-agent-id: github-workflow-registry`.
- The Edge Function validates the JWT signature against GitHub's published JWKS and checks issuer, audience, expiration, repository ID/name, workflow file on `refs/heads/main`, and allowed event type before using the server-side service-role credential.
- The workflow must retain only the `contents: read` and `id-token: write` permissions it needs. Do not grant this identity to unrelated workflows.
- No OIDC token is stored in repository secrets or logged. Tokens are short-lived and should never be copied into chat, source files, or artifacts.

Legacy unattended runtimes may continue to use `SHARED_BRAIN_AGENT_KEY` while they migrate. The registry workflow no longer depends on matching that long-lived secret between GitHub and Supabase. The Edge Function must still have its server-side `SUPABASE_SERVICE_ROLE_KEY` configured; it is never sent to clients or workflows.

If authentication fails, the registry must fail closed and the workflow should report the failure rather than pretending the memory sync succeeded.
