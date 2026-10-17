const JSON_HEADERS = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" };
const MAX_BODY_BYTES = 12000;
const MAX_REQUESTS_PER_HOUR = 5;

function response(body, status, headers = {}) {
  return new Response(JSON.stringify(body), { status, headers: { ...JSON_HEADERS, ...headers } });
}
function allowedOrigins(env) {
  const configured = String(env.ALLOWED_ORIGINS || env.ALLOWED_ORIGIN || "");
  return configured.split(",").map(value => value.trim().replace(/\/$/, "")).filter(Boolean);
}
function originAllowed(request, env) {
  const origin = (request.headers.get("Origin") || "").replace(/\/$/, "");
  return Boolean(origin) && allowedOrigins(env).includes(origin);
}
function corsHeaders(request, env) {
  const origin = request.headers.get("Origin") || "";
  if (!originAllowed(request, env)) return {};
  return {
    "access-control-allow-origin": origin,
    "access-control-allow-methods": "GET, POST, PATCH, DELETE, OPTIONS",
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
    return url.protocol === "https:" && !url.username && !url.password ? url.toString().slice(0, 500) : null;
  } catch {
    return null;
  }
}
async function readLimitedBody(request, maxBytes) {
  if (!request.body) return "";
  const reader = request.body.getReader();
  const chunks = [];
  let total = 0;
  while (true) {
    const part = await reader.read();
    if (part.done) break;
    total += part.value.byteLength;
    if (total > maxBytes) {
      try { await reader.cancel(); } catch {}
      const error = new Error("too_large");
      error.code = "too_large";
      throw error;
    }
    chunks.push(part.value);
  }
  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return new TextDecoder().decode(bytes);
}
async function hashIp(ip, salt) {
  const bytes = new TextEncoder().encode(String(salt || "") + ":" + ip);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest)).map(x => x.toString(16).padStart(2, "0")).join("");
}
async function notifyOwner(env, item) {
  if (!env.RESEND_API_KEY || !env.NOTIFY_EMAIL || !env.FROM_EMAIL) return "not_configured";
  const text = [
    "New Nexora AI project enquiry",
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
        subject: "New Nexora AI enquiry — " + item.service + " — " + item.id.slice(0, 8),
        text
      })
    });
    if (!result.ok) return "failed";
    return "sent";
  } catch {
    return "failed";
  }
}

function bytesToHex(bytes) {
  return Array.from(new Uint8Array(bytes)).map(value => value.toString(16).padStart(2, "0")).join("");
}
function hexToBytes(hex) {
  if (!/^(?:[0-9a-f]{2})+$/i.test(hex)) throw new Error("invalid_hex");
  return Uint8Array.from(hex.match(/.{2}/g), value => parseInt(value, 16));
}
async function sha256Hex(value) {
  return bytesToHex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)));
}
async function passwordHash(password, saltHex) {
  const material = await crypto.subtle.importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits({name:"PBKDF2", salt:hexToBytes(saltHex), iterations:100000, hash:"SHA-256"}, material, 256);
  return bytesToHex(bits);
}
function randomHex(size = 32) {
  const bytes = crypto.getRandomValues(new Uint8Array(size));
  return bytesToHex(bytes);
}
function bearerToken(request) {
  const header = request.headers.get("Authorization") || "";
  return header.startsWith("Bearer ") ? header.slice(7).trim() : "";
}
async function accountFromRequest(request, env) {
  const token = bearerToken(request);
  if (!token || token.length < 40 || token.length > 200) return null;
  const tokenHash = await sha256Hex(token);
  return await env.DB.prepare(
    "SELECT a.id, a.email FROM client_sessions s JOIN client_accounts a ON a.id = s.account_id WHERE s.token_hash = ? AND s.expires_at > ? AND a.disabled = 0"
  ).bind(tokenHash, new Date().toISOString()).first();
}
async function authRateAllowed(request, env, action) {
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const ipHash = await sha256Hex(String(env.IP_HASH_SALT || env.ADMIN_API_KEY || "nexora-auth") + ":" + ip + ":" + action);
  const row = await env.DB.prepare("SELECT COUNT(*) AS total FROM client_auth_attempts WHERE ip_hash = ? AND created_at >= datetime('now','-1 hour')").bind(ipHash).first();
  if (Number(row && row.total || 0) >= 10) return false;
  await env.DB.prepare("INSERT INTO client_auth_attempts (id, ip_hash, created_at) VALUES (?, ?, ?)").bind(crypto.randomUUID(), ipHash, new Date().toISOString()).run();
  return true;
}
async function handleAuth(request, env, cors, action) {
  if (!originAllowed(request, env)) return response({error:"This origin is not allowed."}, 403, cors);
  if (action === "me" && request.method === "GET") {
    const account = await accountFromRequest(request, env);
    return account ? response({ok:true, account:{id:account.id,email:account.email}}, 200, cors) : response({error:"Sign in to continue."}, 401, cors);
  }
  if (action === "logout" && request.method === "POST") {
    const token = bearerToken(request);
    if (token) await env.DB.prepare("DELETE FROM client_sessions WHERE token_hash = ?").bind(await sha256Hex(token)).run();
    return response({ok:true}, 200, cors);
  }
  if (request.method !== "POST") return response({error:"Method not allowed."}, 405, cors);
  let body;
  try { body = JSON.parse(await readLimitedBody(request, 3000)); } catch { return response({error:"Invalid request."}, 400, cors); }
  if (!body || typeof body !== "object" || Array.isArray(body)) return response({error:"Invalid request."}, 400, cors);
  const email = clean(body.email, 180).toLowerCase();
  const password = typeof body.password === "string" ? body.password : "";
  if (!validEmail(email) || password.length < 12 || password.length > 256) {
    return response({error:"Use a valid email and a password between 12 and 256 characters."}, 422, cors);
  }
  if (!await authRateAllowed(request, env, action)) return response({error:"Too many attempts. Try again in an hour."}, 429, {...cors,"retry-after":"3600"});
  let account;
  if (action === "register") {
    const salt = randomHex(16);
    const hash = await passwordHash(password, salt);
    const id = crypto.randomUUID();
    try {
      await env.DB.prepare("INSERT INTO client_accounts (id,email,password_salt,password_hash,created_at,disabled) VALUES (?,?,?,?,?,0)")
        .bind(id,email,salt,hash,new Date().toISOString()).run();
      account = {id,email};
    } catch {
      return response({error:"An account may already exist for this email. Try signing in instead."}, 409, cors);
    }
  } else if (action === "login") {
    account = await env.DB.prepare("SELECT id,email,password_salt,password_hash FROM client_accounts WHERE email = ? AND disabled = 0").bind(email).first();
    const candidate = await passwordHash(password, account ? account.password_salt : "00000000000000000000000000000000");
    if (!account || candidate !== account.password_hash) return response({error:"Email or password is incorrect."}, 401, cors);
  } else {
    return response({error:"Unknown authentication action."}, 404, cors);
  }
  const token = randomHex(32);
  const now = new Date();
  const expires = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
  await env.DB.prepare("INSERT INTO client_sessions (token_hash,account_id,created_at,expires_at) VALUES (?,?,?,?)")
    .bind(await sha256Hex(token), account.id, now.toISOString(), expires.toISOString()).run();
  return response({ok:true, token, expires_at:expires.toISOString(), account:{id:account.id,email:account.email}}, 200, cors);
}

async function createSubmission(request, env, cors) {
  if (!originAllowed(request, env)) {
    return response({ error: "This origin is not allowed to submit enquiries." }, 403, cors);
  }
  const account = await accountFromRequest(request, env);
  if (!account) return response({error:"Sign in before submitting a project request."}, 401, cors);
  const contentLength = Number(request.headers.get("Content-Length") || 0);
  if (contentLength > MAX_BODY_BYTES) return response({ error: "Request is too large." }, 413, cors);
  if (!(request.headers.get("Content-Type") || "").toLowerCase().includes("application/json")) {
    return response({ error: "Send the enquiry as JSON." }, 415, cors);
  }
  let raw;
  try {
    raw = await readLimitedBody(request, MAX_BODY_BYTES);
  } catch (error) {
    if (error && error.code === "too_large") return response({ error: "Request is too large." }, 413, cors);
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
    account_id: account.id,
    created_at: new Date().toISOString(),
    consent_at: payload.consent === true ? new Date().toISOString() : "",
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
  if (payload.consent !== true || !item.name || !validEmail(item.email) || !services.has(item.service) || item.goal.length < 10 || !validDeadline(item.deadline) || item.reference_url === null) {
    return response({ error: "Please check your name, email, service, project goal, deadline, and HTTPS reference link." }, 422, cors);
  }

  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const ipHash = await hashIp(ip, env.IP_HASH_SALT || env.ADMIN_API_KEY || "");
  const recent = await env.DB.prepare(
    "SELECT COUNT(*) AS total FROM submissions WHERE ip_hash = ? AND datetime(created_at) >= datetime('now', '-1 hour')"
  ).bind(ipHash).first();
  if (Number(recent && recent.total || 0) >= MAX_REQUESTS_PER_HOUR) {
    return response({ error: "Too many enquiries from this connection. Please try again later." }, 429, { ...cors, "retry-after": "3600" });
  }

  try {
    await env.DB.prepare(
      "INSERT INTO submissions (id, account_id, created_at, consent_at, name, email, company, service, budget, deadline, goal, reference_url, status, ip_hash, notification_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    ).bind(
      item.id, item.account_id, item.created_at, item.consent_at, item.name, item.email, item.company, item.service, item.budget,
      item.deadline, item.goal, item.reference_url, item.status, ipHash, item.notification_status
    ).run();
  } catch {
    return response({ error: "We could not save this enquiry right now. Please retry later." }, 503, cors);
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
async function deleteSubmission(request, env, id, cors) {
  const origin = request.headers.get("Origin") || "";
  if (origin && !originAllowed(request, env)) return response({ error: "This origin is not allowed." }, 403);
  const auth = request.headers.get("Authorization") || "";
  if (!env.ADMIN_API_KEY || auth !== "Bearer " + env.ADMIN_API_KEY) {
    return response({ error: "Unauthorized." }, 401, { ...cors, "www-authenticate": "Bearer" });
  }
  if (!/^[0-9a-f-]{36}$/i.test(id)) return response({ error: "Invalid submission ID." }, 400, cors);
  const result = await env.DB.prepare("DELETE FROM submissions WHERE id = ?").bind(id).run();
  return response({ deleted: Number(result.meta && result.meta.changes || 0) > 0 }, 200, { ...cors, "cache-control": "no-store" });
}
async function updateSubmissionStatus(request, env, id, cors) {
  const origin = request.headers.get("Origin") || "";
  if (origin && !originAllowed(request, env)) return response({ error: "This origin is not allowed." }, 403);
  const auth = request.headers.get("Authorization") || "";
  if (!env.ADMIN_API_KEY || auth !== "Bearer " + env.ADMIN_API_KEY) {
    return response({ error: "Unauthorized." }, 401, { ...cors, "www-authenticate": "Bearer" });
  }
  if (!/^[0-9a-f-]{36}$/i.test(id)) return response({ error: "Invalid submission ID." }, 400, cors);
  let payload;
  try {
    const raw = await readLimitedBody(request, 1000);
    payload = JSON.parse(raw);
  } catch {
    return response({ error: "Send a valid JSON status update." }, 400, cors);
  }
  const allowedStatuses = new Set(["new", "reviewing", "qualified", "proposal_ready", "in_progress", "delivered", "won", "lost"]);
  const status = clean(payload && payload.status, 30);
  if (!allowedStatuses.has(status)) return response({ error: "Unsupported status." , allowed_statuses: Array.from(allowedStatuses) }, 422, cors);
  const result = await env.DB.prepare("UPDATE submissions SET status = ? WHERE id = ?").bind(status, id).run();
  const changed = Number(result.meta && result.meta.changes || 0) > 0;
  return response({ updated: changed, status: changed ? status : null }, 200, { ...cors, "cache-control": "no-store" });
}
async function listSubmissions(request, env, cors) {
  const origin = request.headers.get("Origin") || "";
  if (origin && !originAllowed(request, env)) return response({ error: "This origin is not allowed." }, 403);
  const auth = request.headers.get("Authorization") || "";
  if (!env.ADMIN_API_KEY || auth !== "Bearer " + env.ADMIN_API_KEY) {
    return response({ error: "Unauthorized." }, 401, { ...cors, "www-authenticate": "Bearer" });
  }
  const url = new URL(request.url);
  const limit = Math.min(100, Math.max(1, Number.parseInt(url.searchParams.get("limit") || "50", 10) || 50));
  const status = clean(url.searchParams.get("status"), 30);
  let result;
  if (status) {
    result = await env.DB.prepare(
      "SELECT id, created_at, consent_at, name, email, company, service, budget, deadline, goal, reference_url, status, notification_status FROM submissions WHERE status = ? ORDER BY created_at DESC LIMIT ?"
    ).bind(status, limit).all();
  } else {
    result = await env.DB.prepare(
      "SELECT id, created_at, consent_at, name, email, company, service, budget, deadline, goal, reference_url, status, notification_status FROM submissions ORDER BY created_at DESC LIMIT ?"
    ).bind(limit).all();
  }
  return response({ submissions: result.results || [] }, 200, { ...cors, "cache-control": "no-store" });
}
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const cors = corsHeaders(request, env);
    if (request.method === "OPTIONS") {
      if (!originAllowed(request, env)) return new Response(null, { status: 403 });
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
    const authMatch = url.pathname.match(/^\/api\/auth\/(register|login|me|logout)$/);
    if (authMatch) {
      try { return await handleAuth(request, env, cors, authMatch[1]); }
      catch (error) { console.error("Nexora client authentication failed:", error && error.message ? error.message : "unknown error"); return response({error:"Authentication service temporarily unavailable."}, 503, cors); }
    }
    if (url.pathname === "/api/intake" && request.method === "POST") {
      try { return await createSubmission(request, env, cors); }
      catch { return response({ error: "The enquiry service is temporarily unavailable. Please retry later." }, 503, cors); }
    }
    if (url.pathname === "/api/admin/submissions" && request.method === "GET") {
      try { return await listSubmissions(request, env, cors); }
      catch { return response({ error: "Could not load submissions." }, 503, cors); }
    }
    const statusMatch = url.pathname.match(/^\/api\/admin\/submissions\/([^/]+)\/status$/);
    if (statusMatch && request.method === "PATCH") {
      try { return await updateSubmissionStatus(request, env, statusMatch[1], cors); }
      catch { return response({ error: "Could not update submission status." }, 503, cors); }
    }
    const deleteMatch = url.pathname.match(/^\/api\/admin\/submissions\/([^/]+)$/);
    if (deleteMatch && request.method === "DELETE") {
      try { return await deleteSubmission(request, env, deleteMatch[1], cors); }
      catch { return response({ error: "Could not delete the submission." }, 503, cors); }
    }
    return response({ error: "Not found." }, 404, cors);
  }
};
