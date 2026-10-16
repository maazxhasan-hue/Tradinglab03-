import test from "node:test";
import assert from "node:assert/strict";
import worker from "./index.js";

const origin = "https://maazxhasan-hue.github.io";
const key = "unit-test-secret";
class DB {
  rows = [];
  prepare(sql) {
    const db = this;
    const q = { sql, args: [], bind(...args) { q.args = args; return q; } };
    q.first = async () => {
      if (sql.includes("SELECT 1")) return { ok: 1 };
      if (sql.includes("COUNT(*)")) return { total: db.rows.filter(x => x.ip_hash === q.args[0]).length };
      return null;
    };
    q.run = async () => {
      if (sql.startsWith("INSERT")) {
        const p = q.args;
        db.rows.push({ id:p[0], created_at:p[1], consent_at:p[2], name:p[3], email:p[4], company:p[5], service:p[6], budget:p[7], deadline:p[8], goal:p[9], reference_url:p[10], status:p[11], ip_hash:p[12], notification_status:p[13] });
        return { meta: { changes: 1 } };
      }
      if (sql.startsWith("UPDATE")) {
        const row = db.rows.find(x => x.id === q.args[1]);
        if (row) row.notification_status = q.args[0];
        return { meta: { changes: row ? 1 : 0 } };
      }
      if (sql.startsWith("DELETE")) {
        const before = db.rows.length;
        db.rows = db.rows.filter(x => x.id !== q.args[0]);
        return { meta: { changes: before - db.rows.length } };
      }
      return { meta: { changes: 0 } };
    };
    q.all = async () => ({ results: db.rows.map(({ ip_hash, ...row }) => row).slice(0, q.args.at(-1)) });
    return q;
  }
}
const makeEnv = () => ({ ALLOWED_ORIGIN: origin, ADMIN_API_KEY: key, DB: new DB() });
const payload = { name:"Sample", email:"sample@example.com", company:"", service:"Business website", budget:"", deadline:"", goal:"I need a simple responsive business website.", reference:"", consent:true, website:"" };
const request = (body = {}, ip = "client-a") => new Request("https://worker.test/api/intake", {
  method:"POST", headers:{ Origin:origin, "Content-Type":"application/json", "CF-Connecting-IP":ip }, body:JSON.stringify({ ...payload, ...body })
});

test("saves an enquiry only after consent", async () => {
  const env = makeEnv();
  assert.equal((await worker.fetch(request({ consent:false }), env)).status, 422);
  const res = await worker.fetch(request(), env);
  assert.equal(res.status, 201);
  assert.equal(env.DB.rows.length, 1);
  assert.ok(env.DB.rows[0].consent_at);
});

test("restricts private enquiry retrieval to the owner", async () => {
  const env = makeEnv();
  await worker.fetch(request(), env);
  const url = "https://worker.test/api/admin/submissions";
  assert.equal((await worker.fetch(new Request(url), env)).status, 401);
  const res = await worker.fetch(new Request(url, { headers:{ Authorization:"Bearer " + key } }), env);
  assert.equal(res.status, 200);
  assert.equal((await res.json()).submissions.length, 1);
});

test("rejects other origins and rate-limits repeated requests", async () => {
  const env = makeEnv();
  const blocked = new Request("https://worker.test/api/intake", { method:"POST", headers:{ Origin:"https://other.example", "Content-Type":"application/json" }, body:JSON.stringify(payload) });
  assert.equal((await worker.fetch(blocked, env)).status, 403);
  for (let i=0; i<5; i++) assert.equal((await worker.fetch(request({ email:"sample" + i + "@example.com" }), env)).status, 201);
  assert.equal((await worker.fetch(request({ email:"sixth@example.com" }), env)).status, 429);
});
