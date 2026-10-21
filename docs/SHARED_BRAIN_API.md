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

### Required secret configuration before machine agents can connect
1. Generate one long random `SHARED_BRAIN_AGENT_KEY` privately.
2. Add the same value to Supabase Edge Function secrets as `SHARED_BRAIN_AGENT_KEY`.
3. Add it to GitHub repository Actions secrets as `SHARED_BRAIN_AGENT_KEY`.
4. Do not paste it into chat, source files, issue comments, or artifacts.
5. Set `SHARED_BRAIN_AGENT_ID` per runtime where the Python client is used.

If the secret is absent, the function rejects machine writes and workflow integrations explicitly skip rather than pretending they synced. No secret value is stored in this repository.
