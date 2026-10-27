export interface Env {
  DB: D1Database;
  ADMIN_TOKEN: string;
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "https://urban-growth-hq.onrender.com",
      "access-control-allow-methods": "GET, POST, OPTIONS",
      "access-control-allow-headers": "content-type, authorization",
    },
  });

function clean(v: unknown, max = 200): string {
  return typeof v === "string" ? v.trim().slice(0, max) : "";
}

async function digest(value: string): Promise<string> {
  const bytes = new TextEncoder().encode(value);
  const hash = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { status: 204 });
    if (url.pathname === "/health" && request.method === "GET") {
      try {
        await env.DB.prepare("SELECT 1 AS ok").first();
        return json({ ok: true, service: "urban-growth-hq-api", database: "connected" });
      } catch {
        return json({ ok: false, service: "urban-growth-hq-api", database: "unavailable" }, 503);
      }
    }

    if (url.pathname === "/api/leads" && request.method === "POST") {
      let body: Record<string, unknown>;
      try { body = await request.json() as Record<string, unknown>; }
      catch { return json({ ok: false, error: "invalid_json" }, 400); }

      const name = clean(body.name, 120);
      const email = clean(body.email, 254).toLowerCase();
      const phone = clean(body.phone, 40);
      const interest = clean(body.interest, 160);
      const source = clean(body.source, 80) || "website";
      const consent = body.contactConsent === true || body.contactConsent === "true" || body.contactConsent === "yes";
      const validEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
      const digits = phone.replace(/\D/g, "");
      const validPhone = /^[+\d() .-]{7,40}$/.test(phone) && digits.length >= 7 && digits.length <= 15;
      if (!name || (!validEmail && !validPhone)) {
        return json({ ok: false, errors: [!name ? "name_required" : null, (!validEmail && !validPhone) ? "valid_email_or_phone_required" : null].filter(Boolean) }, 400);
      }
      const dedupeKey = await digest(validEmail ? "email:" + email : "phone:" + digits);
      const id = crypto.randomUUID();
      try {
        await env.DB.prepare(
          "INSERT INTO leads (id, dedupe_key, name, email, phone, interest, source, contact_consent, contact_allowed, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)"
        ).bind(id, dedupeKey, name, validEmail ? email : "", validPhone ? phone : "", interest, source, consent ? 1 : 0, consent ? 1 : 0, new Date().toISOString()).run();
        return json({ ok: true, status: "accepted", lead_id: id, storage_status: "persisted", follow_up_status: "not_sent", contact_allowed: consent });
      } catch (error) {
        const message = String(error);
        if (message.includes("UNIQUE") || message.includes("constraint")) {
          const existing = await env.DB.prepare("SELECT id, status, created_at FROM leads WHERE dedupe_key = ?").bind(dedupeKey).first();
          return json({ ok: true, status: "duplicate", lead_id: existing?.id, storage_status: "persisted", follow_up_status: "not_sent" });
        }
        return json({ ok: false, error: "persistence_failed" }, 503);
      }
    }

    if (url.pathname === "/api/leads" && request.method === "GET") {
      if (!env.ADMIN_TOKEN || request.headers.get("authorization") !== `Bearer ${env.ADMIN_TOKEN}`) {
        return json({ ok: false, error: "unauthorized" }, 401);
      }
      const limit = Math.min(100, Math.max(1, Number(url.searchParams.get("limit")) || 50));
      const rows = await env.DB.prepare("SELECT id, name, email, phone, interest, source, contact_consent, contact_allowed, status, created_at FROM leads ORDER BY created_at DESC LIMIT ?").bind(limit).all();
      return json({ ok: true, leads: rows.results });
    }

    return json({ ok: false, error: "not_found" }, 404);
  },
};
