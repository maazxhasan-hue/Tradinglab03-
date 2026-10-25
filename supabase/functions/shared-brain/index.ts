import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { verifyGitHubActionsOidc } from "./auth.ts";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info, x-agent-key, x-agent-id, x-github-oidc-token",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Content-Type": "application/json",
  "Cache-Control": "no-store",
};
function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: cors });
}
function safeLabel(value: unknown, max = 100): string {
  return typeof value === "string" ? value.trim().slice(0, max) : "";
}
Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405);

  const base = Deno.env.get("SUPABASE_URL");
  const anon = Deno.env.get("SUPABASE_ANON_KEY") ?? Deno.env.get("SUPABASE_PUBLISHABLE_KEY");
  const serviceRole = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const agentSecret = Deno.env.get("SHARED_BRAIN_AGENT_KEY");
  const providedAgentKey = req.headers.get("x-agent-key") ?? "";
  const providedOidcToken = req.headers.get("x-github-oidc-token") ?? "";
  const bearer = req.headers.get("authorization") ?? "";
  if (!base) return json({ error: "Shared brain is not configured" }, 503);

  let userId: string | null = null;
  let sourceAgent = safeLabel(req.headers.get("x-agent-id"), 100);
  let oidcMachineAuth = false;
  if (providedOidcToken) {
    if (!serviceRole) return json({ error: "Machine memory credentials are not configured" }, 503);
    const oidcIdentity = await verifyGitHubActionsOidc(providedOidcToken);
    if (!oidcIdentity) return json({ error: "Invalid or unauthorized GitHub workflow identity" }, 401);
    const registryIdentity = oidcIdentity === "registry" && sourceAgent === "github-workflow-registry";
    const smokeIdentity = oidcIdentity === "live-smoke" && (
      sourceAgent === "shared-brain-smoke-writer" ||
      sourceAgent === "shared-brain-smoke-reader" ||
      /^nexora-[a-z0-9._:-]{1,80}$/.test(sourceAgent)
    );
    if (!registryIdentity && !smokeIdentity) {
      return json({ error: "GitHub OIDC identity is not authorized for this agent ID" }, 403);
    }
    oidcMachineAuth = true;
  }
  const machineAuth = Boolean(
    serviceRole && (
      oidcMachineAuth ||
      (agentSecret && providedAgentKey && providedAgentKey === agentSecret)
    ),
  );
  let dbKey = "";
  let dbAuth = "";
  let table = "";
  if (machineAuth) {
    if (!/^[a-zA-Z0-9._:-]{1,100}$/.test(sourceAgent)) return json({ error: "A valid x-agent-id is required" }, 400);
    dbKey = serviceRole!;
    dbAuth = serviceRole!;
    table = "agent_shared_facts";
  } else {
    if (!anon || !bearer.startsWith("Bearer ")) return json({ error: "Valid user session or configured agent credentials required" }, 401);
    const who = await fetch(`${base}/auth/v1/user`, { headers: { apikey: anon, authorization: bearer } }).catch(() => null);
    if (!who || !who.ok) return json({ error: "Invalid or expired session" }, 401);
    const user = await who.json().catch(() => null);
    if (!user?.id) return json({ error: "Could not validate session" }, 401);
    userId = user.id;
    dbKey = anon;
    dbAuth = bearer;
    table = "agent_shared_memory";
  }

  let body: Record<string, unknown>;
  try { body = await req.json(); } catch { return json({ error: "Invalid JSON" }, 400); }
  const action = body.action;
  const projectKey = safeLabel(body.project_key || "nexora", 100);
  const namespace = safeLabel(body.namespace || "general", 100);
  if (!/^[a-zA-Z0-9._:-]{1,100}$/.test(projectKey) || !/^[a-zA-Z0-9._:-]{1,100}$/.test(namespace)) {
    return json({ error: "Invalid project_key or namespace" }, 400);
  }
  const headers = { apikey: dbKey, authorization: dbAuth, "content-type": "application/json", prefer: "return=representation" };
  const root = `${base}/rest/v1/${table}`;

  if (action === "recall") {
    const limit = Math.min(50, Math.max(1, Number.isInteger(body.limit) ? Number(body.limit) : 20));
    const params = new URLSearchParams({
      select: "id,project_key,namespace,memory_key,content,summary,tags,source_agent,confidence,source_ref,version,created_at,updated_at,expires_at",
      project_key: `eq.${projectKey}`, namespace: `eq.${namespace}`, order: "updated_at.desc", limit: String(limit),
      or: `(expires_at.is.null,expires_at.gt.${new Date().toISOString()})`,
    });
    if (userId) params.set("user_id", `eq.${userId}`);
    if (typeof body.query === "string" && body.query.trim()) {
      const q = body.query.trim().slice(0, 120).replace(/[%,()]/g, "");
      if (q) params.set("summary", `ilike.*${q}*`);
    }
    const result = await fetch(`${root}?${params}`, { headers }).catch(() => null);
    if (!result) return json({ error: "Shared memory database unavailable" }, 503);
    const rows = await result.json().catch(() => null);
    if (!result.ok) return json({ error: "Could not recall shared memory" }, 502);
    return json({ memories: rows, count: Array.isArray(rows) ? rows.length : 0, scope: machineAuth ? "shared-agent" : "user" });
  }

  if (action === "remember") {
    const key = safeLabel(body.memory_key, 160);
    const source = machineAuth ? sourceAgent : safeLabel(body.source_agent, 100);
    const summary = safeLabel(body.summary, 2000);
    const value = body.content;
    if (!/^[a-zA-Z0-9._:/ -]{1,160}$/.test(key)) return json({ error: "memory_key is required (1–160 safe characters)" }, 400);
    if (!/^[a-zA-Z0-9._:-]{1,100}$/.test(source)) return json({ error: "source_agent is required" }, 400);
    if (value === undefined || JSON.stringify(value).length > 20000) return json({ error: "content is required and must be at most 20 KB" }, 413);
    const tags = Array.isArray(body.tags) ? body.tags.filter((x): x is string => typeof x === "string").slice(0, 20).map(x => x.slice(0, 60)) : [];
    const confidence = typeof body.confidence === "number" && body.confidence >= 0 && body.confidence <= 1 ? body.confidence : 0.8;
    const query = new URLSearchParams({ select: "id,version", project_key: `eq.${projectKey}`, namespace: `eq.${namespace}`, memory_key: `eq.${key}`, limit: "1" });
    if (userId) query.set("user_id", `eq.${userId}`);
    const check = await fetch(`${root}?${query}`, { headers }).catch(() => null);
    if (!check?.ok) return json({ error: "Could not check existing memory version" }, 502);
    const priorRows = await check.json().catch(() => []);
    const prior = Array.isArray(priorRows) ? priorRows[0] : null;
    const row: Record<string, unknown> = {
      project_key: projectKey, namespace, memory_key: key, content: value, summary, tags,
      source_agent: source, confidence, source_ref: typeof body.source_ref === "string" ? body.source_ref.slice(0, 500) : null,
      version: prior ? Number(prior.version) + 1 : 1, updated_at: new Date().toISOString(),
    };
    if (userId) row.user_id = userId;
    if (typeof body.expires_at === "string") {
      const expiry = new Date(body.expires_at);
      if (!Number.isFinite(expiry.getTime())) return json({ error: "expires_at must be a valid date-time" }, 400);
      row.expires_at = expiry.toISOString();
    }
    const writeParams = new URLSearchParams({ on_conflict: userId ? "user_id,project_key,namespace,memory_key" : "project_key,namespace,memory_key" });
    const saved = await fetch(`${root}?${writeParams}`, {
      method: "POST", headers: { ...headers, prefer: "resolution=merge-duplicates,return=representation" }, body: JSON.stringify(row),
    }).catch(() => null);
    if (!saved) return json({ error: "Shared memory database unavailable" }, 503);
    const result = await saved.json().catch(() => null);
    if (!saved.ok) return json({ error: "Could not save shared memory" }, 502);
    return json({ saved: true, memory: Array.isArray(result) ? result[0] : result, scope: machineAuth ? "shared-agent" : "user" }, 201);
  }
  return json({ error: "Unsupported action. Use recall or remember." }, 400);
});
