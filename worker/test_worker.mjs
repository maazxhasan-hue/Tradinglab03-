import test from "node:test";
import assert from "node:assert/strict";
import worker from "./index.js";

const origin = "https://maazxhasan-hue.github.io";
const key = "unit-test-secret";
class DB {
  rows = [];
  accounts = [];
  sessions = [];
  attempts = [];
  rateEvents = [];
  prepare(sql) {
    const db = this;
    const q = { sql, args: [], bind(...args) { q.args = args; return q; } };
    q.first = async () => {
      if (sql.includes("SELECT 1")) return { ok: 1 };
      if (sql.includes("FROM client_rate_limit_events") && sql.includes("COUNT(*)")) {
        const [bucket, route, since] = q.args;
        return { total: db.rateEvents.filter(x => x.bucket_hash === bucket && x.route_type === route && x.created_at >= since && (sql.includes("outcome = 'failure'") ? x.outcome === "failure" : (!sql.includes("outcome = 'attempt'") || x.outcome === "attempt"))).length };
      }
      if (sql.includes("FROM client_rate_limit_events") && sql.includes("ORDER BY created_at DESC")) {
        return db.rateEvents.filter(x => x.bucket_hash === q.args[0] && x.route_type === q.args[1] && x.outcome === "failure").sort((a,b)=>b.created_at.localeCompare(a.created_at))[0] || null;
      }
      if (sql.includes("FROM client_rate_limit_events") && sql.includes("ORDER BY created_at ASC")) {
        return db.rateEvents.filter(x => x.bucket_hash === q.args[0] && x.route_type === q.args[1] && x.created_at >= q.args[2]).sort((a,b)=>a.created_at.localeCompare(b.created_at))[0] || null;
      }
      if (sql.includes("FROM client_auth_attempts")) return { total: db.attempts.filter(x => x.ip_hash === q.args[0]).length };
      if (sql.includes("FROM client_sessions s JOIN client_accounts")) {
        const session=db.sessions.find(x=>x.token_hash===q.args[0] && x.expires_at>q.args[1]);
        const account=session && db.accounts.find(x=>x.id===session.account_id && x.disabled===0);
        return account ? {id:account.id,email:account.email} : null;
      }
      if (sql.includes("FROM client_accounts WHERE email")) {
        const account=db.accounts.find(x=>x.email===q.args[0] && x.disabled===0);
        return account || null;
      }
      if (sql.includes("COUNT(*)")) return { total: db.rows.filter(x => x.ip_hash === q.args[0]).length };
      return null;
    };
    q.run = async () => {
      if (sql.startsWith("INSERT INTO client_rate_limit_events")) { db.rateEvents.push({id:q.args[0],bucket_hash:q.args[1],route_type:q.args[2],outcome:q.args[3],created_at:q.args[4]}); return {meta:{changes:1}}; }
      if (sql.startsWith("INSERT INTO client_auth_attempts")) { db.attempts.push({id:q.args[0],ip_hash:q.args[1],created_at:q.args[2]}); return {meta:{changes:1}}; }
      if (sql.startsWith("INSERT INTO client_accounts")) {
        if(db.accounts.some(x=>x.email===q.args[1])) throw new Error("duplicate email");
        db.accounts.push({id:q.args[0],email:q.args[1],password_salt:q.args[2],password_hash:q.args[3],created_at:q.args[4],disabled:0});
        return {meta:{changes:1}};
      }
      if (sql.startsWith("INSERT INTO client_sessions")) { db.sessions.push({token_hash:q.args[0],account_id:q.args[1],created_at:q.args[2],expires_at:q.args[3]}); return {meta:{changes:1}}; }
      if (sql.startsWith("INSERT INTO submissions")) {
        const p = q.args;
        db.rows.push({ id:p[0], account_id:p[1], created_at:p[2], consent_at:p[3], name:p[4], email:p[5], company:p[6], service:p[7], budget:p[8], deadline:p[9], goal:p[10], reference_url:p[11], status:p[12], ip_hash:p[13], notification_status:p[14] });
        return { meta: { changes: 1 } };
      }
      if (sql.startsWith("UPDATE")) {
        const row = db.rows.find(x => x.id === q.args[1]);
        if (row) row.notification_status = q.args[0];
        return { meta: { changes: row ? 1 : 0 } };
      }
      if (sql.startsWith("DELETE FROM client_sessions")) { const n=db.sessions.length; db.sessions=db.sessions.filter(x=>x.token_hash!==q.args[0]); return {meta:{changes:n-db.sessions.length}}; }
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
const request = (body = {}, ip = "client-a", token = "") => new Request("https://worker.test/api/intake", {
  method:"POST", headers:{ Origin:origin, "Content-Type":"application/json", "CF-Connecting-IP":ip, ...(token?{Authorization:"Bearer "+token}:{}) }, body:JSON.stringify({ ...payload, ...body })
});
async function register(env, email="client@example.com") {
  const res=await worker.fetch(new Request("https://worker.test/api/auth/register",{method:"POST",headers:{Origin:origin,"Content-Type":"application/json","CF-Connecting-IP":"auth-client"},body:JSON.stringify({email,password:"A-Strong-Unit-Test-Password-2026"})}),env);
  assert.equal(res.status,200);
  return (await res.json()).token;
}

test("saves an enquiry only after consent", async () => {
  const env = makeEnv();
  const token=await register(env);
  assert.equal((await worker.fetch(request({ consent:false }, "client-a", token), env)).status, 422);
  const res = await worker.fetch(request({}, "client-a", token), env);
  assert.equal(res.status, 201);
  assert.equal(env.DB.rows.length, 1);
  assert.ok(env.DB.rows[0].consent_at);
});

test("restricts private enquiry retrieval to the owner", async () => {
  const env = makeEnv();
  const token=await register(env);
  await worker.fetch(request({}, "client-a", token), env);
  const url = "https://worker.test/api/admin/submissions";
  assert.equal((await worker.fetch(new Request(url), env)).status, 401);
  const res = await worker.fetch(new Request(url, { headers:{ Authorization:"Bearer " + key } }), env);
  assert.equal(res.status, 200);
  assert.equal((await res.json()).submissions.length, 1);
});

test("rejects other origins and rate-limits repeated requests", async () => {
  const env = makeEnv();
  const token=await register(env);
  const blocked = new Request("https://worker.test/api/intake", { method:"POST", headers:{ Origin:"https://other.example", "Content-Type":"application/json" }, body:JSON.stringify(payload) });
  assert.equal((await worker.fetch(blocked, env)).status, 403);
  for (let i=0; i<5; i++) assert.equal((await worker.fetch(request({ email:"sample" + i + "@example.com" }, "client-a", token), env)).status, 201);
  assert.equal((await worker.fetch(request({ email:"sixth@example.com" }, "client-a", token), env)).status, 429);
});

test("rejects anonymous intake and supports login and logout", async () => {
  const env=makeEnv();
  assert.equal((await worker.fetch(request(),env)).status,401);
  await register(env,"auth@example.com");
  const login=await worker.fetch(new Request("https://worker.test/api/auth/login",{method:"POST",headers:{Origin:origin,"Content-Type":"application/json","CF-Connecting-IP":"login-client"},body:JSON.stringify({email:"auth@example.com",password:"A-Strong-Unit-Test-Password-2026"})}),env);
  assert.equal(login.status,200);
  const loginBody=await login.json(); assert.ok(loginBody.token);
  const me=await worker.fetch(new Request("https://worker.test/api/auth/me",{headers:{Origin:origin,Authorization:"Bearer "+loginBody.token}}),env); assert.equal(me.status,200);
  const logout=await worker.fetch(new Request("https://worker.test/api/auth/logout",{method:"POST",headers:{Origin:origin,Authorization:"Bearer "+loginBody.token}}),env); assert.equal(logout.status,200);
  const after=await worker.fetch(new Request("https://worker.test/api/auth/me",{headers:{Origin:origin,Authorization:"Bearer "+loginBody.token}}),env); assert.equal(after.status,401);
});


test("serves website AI chat through the Workers AI binding", async () => {
  const env = makeEnv();
  env.AI = {
    run: async (model, options) => {
      assert.equal(model, "@cf/meta/llama-3.1-8b-instruct-fast");
      assert.ok(options.messages.some(item => item.role === "user" && item.content === "What does Nexora do?"));
      return { response: "Nexora helps businesses with websites and automation." };
    }
  };
  const res = await worker.fetch(new Request("https://worker.test/api/chat", {
    method: "POST",
    headers: { Origin: origin, "Content-Type": "application/json" },
    body: JSON.stringify({ message: "What does Nexora do?", history: [] })
  }), env);
  assert.equal(res.status, 200);
  assert.match((await res.json()).reply, /Nexora helps businesses/);
});

test("reports a clear service error when the Workers AI binding is absent", async () => {
  const env = makeEnv();
  const res = await worker.fetch(new Request("https://worker.test/api/chat", {
    method: "POST",
    headers: { Origin: origin, "Content-Type": "application/json" },
    body: JSON.stringify({ message: "Hello", history: [] })
  }), env);
  assert.equal(res.status, 503);
  assert.match((await res.json()).error, /AI chat is not configured/);
});
