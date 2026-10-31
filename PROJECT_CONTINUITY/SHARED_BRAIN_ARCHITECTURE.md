# Shared Brain Architecture — All Nexora Agents

Status: **Architecture requirement recorded; implementation not yet verified.**

## User requirement
All agents in the Nexora project should use one shared brain rather than maintaining conflicting, isolated memories and policies. Agents should share approved project knowledge, decisions, task state, and learnings through a common service.

## Intended architecture
- **Shared Brain API:** one central service is the authoritative entry point for reading/writing shared agent memory and project knowledge.
- **Shared persistent store:** use the existing Supabase project only after confirming schema, access rules, and tenant boundaries. Store durable facts, decisions, task state, useful learnings, provenance, timestamps, and version information.
- **Agent identity:** each agent must identify itself and the task/request it is acting on. Apply least-privilege access and per-user/per-project isolation.
- **Read/write contract:** agents retrieve relevant context before acting and submit concise, sourced updates after work. Validate and deduplicate updates; do not blindly overwrite authoritative facts.
- **Source of truth:** code, configuration, and deployment state must be verified against their actual repositories/providers. Agent-written summaries are helpful indexes, not proof that a change shipped.
- **Conflict handling:** record provenance, version, and timestamps. Resolve contradictions explicitly; do not silently merge conflicting instructions or invent facts.
- **Security boundaries:** secrets, credentials, personal data, and privileged configuration must not be copied into general shared memory. Store secret names/status only, and use provider secret stores.
- **Human control:** destructive actions, production changes, financial execution, and permission changes still require the applicable authorization and risk checks. A shared brain is not blanket permission for every agent.
- **Resilience:** handle unavailable shared memory safely; agents should surface that context is stale/unavailable instead of pretending it was read or saved. Keep backups and audit logs.

## Implementation plan
1. Inventory all current agents, their runtimes, repositories, data stores, and existing memory paths.
2. Design a common versioned API and schema compatible with each runtime.
3. Add authentication, per-agent identity, row-level access control, audit logging, and conflict/version handling.
4. Integrate agents incrementally, beginning with read-only context retrieval, then controlled writes.
5. Run cross-agent tests: one agent records a fact, another retrieves it; verify permissions, stale data behavior, conflict resolution, and isolation between projects/users.
6. Update the main project STATE and CHANGELOG with each implementation commit and actual test result.

## Important current limitation
This document records the desired architecture only. No claim is made that every existing agent has already been connected to one brain. The existing Mythos Supabase workspace tables are project/draft/codex storage; they are not, by themselves, proof of a general shared-agent-memory system. Do not repurpose them blindly. Inspect the repository and current deployed agent services before implementation.
