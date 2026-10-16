const JSON_HEADERS = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" };
const MAX_BODY_BYTES = 12000;
const MAX_REQUESTS_PER_HOUR = 5;

function response(body, status, headers = {}) {
  return new Response(JSON.stringify(body), { status, headers: { ...JSON_HEADERS, ...headers } });
}
function corsHeaders(request, env) {
  const origin = request.headers.get("Origin") || "";
  if (!env.ALLOWED_ORIGIN || origin !== env.ALLOWED_ORIGIN) return {};
  return {
    "access-control-allow-origin": origin,
    "access-control-allow-methods": "GET, POST, OPTIONS",
    "access-control-allow-headers": "Content-Type, Authorization",
    "access-control-max-age": "86400",
    "vary": "Origin"
  };
}
function clean(value, max) {
  return typeof value === "string" ? value.trim().slice(0, max) : "";
}
function validEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value) && value.length <= 180;
}
function validDeadline(value) {
  return !value || /^\d{4}-\d{2}-\d{2}$/.test(value);
}
function safeReference(value) {
  if (!value) return "";
  try {
    const url = new URL(value);
    return url.protocol === "https:" ? url.toString().slice(0, 500) : null;
  } catch {
    return null;
  }
}
async function hashIp(ip, salt) {
  const bytes = new TextEncoder().encode(String(salt || "") + ":" + ip);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest)).map(x => x.toString(16).padStart(2, "0")).join("");
}
async function notifyOwner(env, item) {
  if (!env.RESEND_API_KEY || !env.NOTIFY_EMAIL || !env.FROM_EMAIL) return "not_configured";
  const text = [
    "New TradingLab03 project enquiry",
    "Reference: " + item.id,
    "Received: " + item.created_at,
    "",
    "Name: " + item.name,
    "Email: " + item.email,
    "Business: " + (item.company || "Not supplied"),
    "Service: " + item.service,
    "Budget: " + (item.budget || "Not decided"),
    "Deadline: " + (item.deadline || "Not supplied"),
    "Reference URL: " + (item.reference_url || "Not supplied"),
    "",
    "Goal and requirements:",
    item.goal,
    "",
    "Reply to the client only after reviewing the request."
  ].join("\n");
  try {
    const result = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { "authorization": "Bearer " + env.RESEND_API_KEY, "content-type": "application/json" },
      body: JSON.stringify({
        from: env.FROM_EMAIL,
        to: [env.NOTIFY_EMAIL],
        reply_to: item.email,
        subject: "New TradingLab03 enquiry — " + item.service + " — " + item.id.slice(0, 8),
        text
      })
    });
    if (!result.ok) return "failed";
    return "sent";
  } catch {
    return "failed";
  }
}
async function createSubmission(request, env, cors) {
  if (request.headers.get("Origin") !== env.ALLOWED_ORIGIN) {
    return response({ error: "This origin is not allowed to submit enquiries." }, 403, cors);
  }
  const contentLength = Number(request.headers.get("Content-Length") || 0);
  if (contentLength > MAX_BODY_BYTES) return response({ error: "Request is too large." }, 413, cors);
  if (!(request.headers.get("Content-Type") || "").toLowerCase().includes("application/json")) {
    return response({ error: "Send the enquiry as JSON." }, 415, cors);
  }
  let raw;
  try {
    raw = await request.text();
    if (new TextEncoder().encode(raw).byteLength > MAX_BODY_BYTES) {
      return response({ error: "Request is too large." }, 413, cors);
    }
  } catch {
    return response({ error: "Could not read the request." }, 400, cors);
  }
  let payload;
  try { payload = JSON.parse(raw); } catch { return response({ error: "Invalid JSON." }, 400, cors); }
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return response({ error: "Invalid enquiry." }, 400, cors);
  }
  // Quietly accept honeypot submissions without storing or notifying.
  if (clean(payload.website, 300)) return response({ ok: true, reference_id: "received" }, 201, cors);

  const item = {
    id: crypto.randomUUID(),
    created_at: new Date().toISOString(),
    name: clean(payload.name, 120),
    email: clean(payload.email, 180).toLowerCase(),
    company: clean(payload.company, 160),
    service: clean(payload.service, 80),
    budget: clean(payload.budget, 80),
    deadline: clean(payload.deadline, 10),
    goal: clean(payload.goal, 5000),
    reference_url: safeReference(clean(payload.reference, 500)),
    status: "new",
    notification_status: "pending"
  };
  const services = new Set([
    "Business website", "Landing page", "Website cleanup / QA", "Short-form content kit",
    "Workflow automation", "Document / data workflow", "Not sure yet"
  ]);
  if (!item.name || !validEmail(item.email) || !services.has(item.service) || item.goal.length < 10 || !validDeadline(item.deadline) || item.reference_url === null) {
    return response({ error: "Please check your name, email, service, project goal, deadline, and HTTPS reference link." }, 422, cors);
  }

  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const ipHash = await hashIp(ip, env.IP_HASH_SALT || "");
  const recent = await env.DB.prepare(
    "SELECT COUNT(*) AS total FROM submissions WHERE ip_hash = ? AND datetime(created_at) >= datetime('now', '-1 hour')"
  ).bind(ipHash).first();
  if (Number(recent && recent.total || 0) >= MAX_REQUESTS_PER_HOUR) {
    return response({ error: "Too many enquiries from this connection. Please try again later or contact us on Instagram." }, 429, { ...cors, "retry-after": "3600" });
  }

  try {
    await env.DB.prepare(
      "INSERT INTO submissions (id, created_at, name, email, company, service, budget, deadline, goal, reference_url, status, ip_hash, notification_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    ).bind(
      item.id, item.created_at, item.name, item.email, item.company, item.service, item.budget,
      item.deadline, item.goal, item.reference_url, item.status, ipHash, item.notification_status
    ).run();
  } catch {
    return response({ error: "We could not save this enquiry right now. Please retry or contact us on Instagram." }, 503, cors);
  }

  const notificationStatus = await notifyOwner(env, item);
  try {
    await env.DB.prepare("UPDATE submissions SET notification_status = ? WHERE id = ?")
      .bind(notificationStatus, item.id).run();
  } catch {
    // The saved enquiry remains available to the owner even if notification metadata cannot update.
  }
  return response({
    ok: true,
    reference_id: item.id,
    message: "Your enquiry was received and saved. Keep this reference for follow-up.",
    notification: notificationStatus === "sent" ? "owner_notified" : notificationStatus === "failed" ? "saved_notification_failed" : "saved_no_email"
  }, 201, cors);
}
async function deleteSubmission(request, env, id) {
  const auth = request.headers.get("Authorization") || "";
  if (!env.ADMIN_API_KEY || auth !== "Bearer " + env.ADMIN_API_KEY) {
    return response({ error: "Unauthorized." }, 401, { "www-authenticate": "Bearer" });
  }
  if (!/^[0-9a-f-]{36}$/i.test(id)) return response({ error: "Invalid submission ID." }, 400);
  const result = await env.DB.prepare("DELETE FROM submissions WHERE id = ?").bind(id).run();
  return response({ deleted: Number(result.meta && result.meta.changes || 0) > 0 }, 200, { "cache-control": "no-store" });
}
async function listSubmissions(request, env) {
  const auth = request.headers.get("Authorization") || "";
  if (!env.ADMIN_API_KEY || auth !== "Bearer " + env.ADMIN_API_KEY) {
    return response({ error: "Unauthorized." }, 401, { "www-authenticate": "Bearer" });
  }
  const url = new URL(request.url);
  const limit = Math.min(100, Math.max(1, Number.parseInt(url.searchParams.get("limit") || "50", 10) || 50));
  const status = clean(url.searchParams.get("status"), 30);
  let result;
  if (status) {
    result = await env.DB.prepare(
      "SELECT id, created_at, name, email, company, service, budget, deadline, goal, reference_url, status, notification_status FROM submissions WHERE status = ? ORDER BY created_at DESC LIMIT ?"
    ).bind(status, limit).all();
  } else {
    result = await env.DB.prepare(
      "SELECT id, created_at, name, email, company, service, budget, deadline, goal, reference_url, status, notification_status FROM submissions ORDER BY created_at DESC LIMIT ?"
    ).bind(limit).all();
  }
  return response({ submissions: result.results || [] }, 200, { "cache-control": "no-store" });
}
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const cors = corsHeaders(request, env);
    if (request.method === "OPTIONS") {
      if (request.headers.get("Origin") !== env.ALLOWED_ORIGIN) return new Response(null, { status: 403 });
      return new Response(null, { status: 204, headers: cors });
    }
    if (url.pathname === "/health" && request.method === "GET") {
      try {
        await env.DB.prepare("SELECT 1 AS ok").first();
        return response({ ok: true, service: "tradinglab03-intake", storage: "ready" }, 200, cors);
      } catch {
        return response({ ok: false, service: "tradinglab03-intake", storage: "unavailable" }, 503, cors);
      }
    }
    if (url.pathname === "/api/intake" && request.method === "POST") {
      try { return await createSubmission(request, env, cors); }
      catch { return response({ error: "The enquiry service is temporarily unavailable. Please retry or use the contact link." }, 503, cors); }
    }
    if (url.pathname === "/api/admin/submissions" && request.method === "GET") {
      try { return await listSubmissions(request, env); }
      catch { return response({ error: "Could not load submissions." }, 503); }
    }
    const deleteMatch = url.pathname.match(/^\/api\/admin\/submissions\/([^/]+)$/);
    if (deleteMatch && request.method === "DELETE") {
      try { return await deleteSubmission(request, env, deleteMatch[1]); }
      catch { return response({ error: "Could not delete the submission." }, 503); }
    }
    return response({ error: "Not found." }, 404, cors);
  }
};
