"""Authenticated Nexora AI HQ served by the private Harvey backend.

The public static HQ page is intentionally only a transition notice. This module
adds a server-protected owner workspace to the existing FastAPI process.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app import app, db, AGENT_ROLES, now, SHARED_BRAIN_AGENT_KEY

COOKIE_NAME = "nexora_hq_session"
SESSION_TTL_SECONDS = 8 * 60 * 60
MAX_LOGIN_BODY_BYTES = 8192


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _session_secret() -> str:
    return os.getenv("HQ_SESSION_SECRET", "")


def _session_token(expiry: int) -> str:
    payload = _b64(json.dumps({"exp": expiry, "sub": "owner"}, separators=(",", ":")).encode())
    signature = hmac.new(_session_secret().encode(), payload.encode(), hashlib.sha256).digest()
    return payload + "." + _b64(signature)


def _valid_session(token: str | None, current_time: int | None = None) -> bool:
    if not token or not _session_secret():
        return False
    try:
        payload, supplied_signature = token.split(".", 1)
        expected = _b64(hmac.new(_session_secret().encode(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(supplied_signature, expected):
            return False
        claims = json.loads(_unb64(payload))
        now_ts = int(time.time() if current_time is None else current_time)
        return claims.get("sub") == "owner" and isinstance(claims.get("exp"), int) and now_ts < claims["exp"]
    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        return False


def _ensure_login_attempts_table() -> None:
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS hq_login_attempts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_hash TEXT NOT NULL,
            attempted_at TEXT NOT NULL
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_hq_login_attempts_ip_time ON hq_login_attempts(ip_hash, attempted_at)")


def _login_bucket(request: Request) -> str:
    # Store only a keyed digest of the peer address, not the raw IP.
    address = request.client.host if request.client else "unknown"
    return hmac.new(_session_secret().encode(), address.encode(), hashlib.sha256).hexdigest()


def _configured() -> bool:
    return bool(os.getenv("HQ_ADMIN_PASSWORD", "") and _session_secret())


def _headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "X-Frame-Options": "DENY",
    }


LOGIN_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="no-referrer">
<title>Private HQ Login · Nexora AI</title>
<style>
:root{color-scheme:dark;font-family:Inter,system-ui,-apple-system,sans-serif;background:#070b12;color:#edf4ff}
*{box-sizing:border-box}body{min-height:100vh;margin:0;display:grid;place-items:center;padding:22px;background:radial-gradient(ellipse at 80% 5%,#123a48,transparent 45%),#070b12}
main{width:min(440px,100%);padding:32px;border:1px solid #284055;border-radius:22px;background:#0d1723;box-shadow:0 24px 80px #0008}
.brand{font-size:.78rem;font-weight:900;letter-spacing:.16em;color:#68e8d4}h1{font-size:2rem;letter-spacing:-.05em;margin:26px 0 8px}p{color:#9fb0c5;line-height:1.6}
label{display:block;margin:22px 0 7px;font-size:.9rem}input{width:100%;padding:13px;border-radius:10px;border:1px solid #344c61;background:#07101a;color:#fff;font:inherit}
button{width:100%;margin-top:16px;padding:13px;border:0;border-radius:10px;background:#68e8d4;color:#06201e;font:inherit;font-weight:850;cursor:pointer}
small{display:block;margin-top:18px;color:#8fa2b8;line-height:1.5}.error{color:#ffb8bd}
</style></head><body><main><div class="brand">NEXORA AI / PRIVATE HQ</div><h1>Welcome back.</h1>
<p>Sign in to the owner workspace. This session is protected by a server-signed, HTTP-only cookie.</p>
<form method="post" action="/hq/login"><label for="password">Owner password</label>
<input id="password" name="password" type="password" autocomplete="current-password" required maxlength="1024" autofocus>
<button type="submit">Unlock HQ</button></form>
<div id="message" role="status" aria-live="polite"></div>
<small>Only the owner password is accepted. Do not share it or place it in browser scripts, URLs, or source control.</small>
</main><script>
const q=new URLSearchParams(location.search);if(q.has('error')){const m=document.getElementById('message');m.className='error';m.textContent='Sign-in failed. Check the password and try again.'}
</script></body></html>"""


HQ_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="no-referrer">
<title>Nexora AI · Private HQ</title>
<style>
:root{color-scheme:dark;font-family:Inter,system-ui,-apple-system,sans-serif;background:#070b12;color:#edf4ff;--panel:#0e1926;--line:#253b50;--muted:#9fb0c5;--teal:#68e8d4;--blue:#8db7ff}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 85% 0%,#123543 0,transparent 36%),#070b12}
header{display:flex;justify-content:space-between;align-items:center;gap:18px;padding:20px max(20px,calc((100vw - 1240px)/2));border-bottom:1px solid var(--line);background:#07101bd9}
.brand{font-weight:950;letter-spacing:.12em;color:var(--teal);font-size:.8rem}.sub{color:var(--muted);font-size:.85rem;margin-top:5px}
button{cursor:pointer;border:1px solid var(--line);border-radius:10px;padding:10px 13px;color:#edf4ff;background:#111f2e;font:inherit;font-weight:700}button.primary{background:var(--teal);color:#071d1b;border-color:var(--teal)}
main{width:min(1240px,calc(100% - 32px));margin:30px auto 64px}.hero{display:flex;justify-content:space-between;align-items:end;gap:18px;flex-wrap:wrap;margin-bottom:22px}
h1{font-size:clamp(2rem,4vw,3.5rem);letter-spacing:-.06em;margin:7px 0}.muted{color:var(--muted)}.eyebrow{color:var(--teal);font-size:.72rem;letter-spacing:.14em;font-weight:900;text-transform:uppercase}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.panel{border:1px solid var(--line);border-radius:16px;padding:19px;background:linear-gradient(145deg,#112033,var(--panel));min-width:0}
.klabel{font-size:.82rem;color:var(--muted)}.value{font-size:2rem;font-weight:900;letter-spacing:-.05em;margin-top:7px;overflow-wrap:anywhere}.status{display:inline-flex;border:1px solid #335466;border-radius:999px;padding:5px 9px;color:var(--teal);font-size:.76rem;margin:4px 5px 0 0}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}.panel h2{font-size:1.05rem;margin:0 0 14px}.list{display:grid;gap:9px}.item{display:flex;justify-content:space-between;gap:12px;padding:11px 0;border-top:1px solid #1e3042}.item:first-child{border-top:0}.item strong{font-size:.88rem;overflow-wrap:anywhere}.item span{color:var(--muted);font-size:.8rem;text-align:right}.wide{margin-top:14px}.notice{margin-top:14px;padding:14px 16px;border:1px solid #5b4c2d;border-radius:12px;color:#f3d99a;background:#211c11;line-height:1.55}
footer{margin-top:18px;color:var(--muted);font-size:.8rem;line-height:1.6}.error{color:#ffb7bf}.loading{color:var(--muted)}
@media(max-width:850px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.two{grid-template-columns:1fr}}
@media(max-width:440px){.grid{grid-template-columns:1fr}.value{font-size:1.7rem}header{align-items:flex-start}}
</style></head><body>
<header><div><div class="brand">NEXORA AI / PRIVATE HQ</div><div class="sub">Owner workspace · server-authenticated</div></div>
<div><button id="refresh">Refresh</button> <button id="logout" class="primary">Sign out</button></div></header>
<main><section class="hero"><div><div class="eyebrow">Operations overview</div><h1>Company command.</h1><div class="muted">A live read-only view of recorded backend activity. Role definitions are not proof of autonomous execution.</div></div><div id="updated" class="muted">Loading live status…</div></section>
<div id="error" class="notice" hidden></div>
<section class="grid" aria-label="Company metrics">
<div class="panel"><div class="klabel">Recorded tasks</div><div class="value" id="tasks">—</div></div>
<div class="panel"><div class="klabel">Company jobs</div><div class="value" id="jobs">—</div></div>
<div class="panel"><div class="klabel">Pending approvals</div><div class="value" id="approvals">—</div></div>
<div class="panel"><div class="klabel">Defined agent roles</div><div class="value" id="roles">—</div></div></section>
<section class="two"><div class="panel"><h2>Backend & integrations</h2><div id="integrations" class="list loading">Loading integration status…</div></div>
<div class="panel"><h2>Task status</h2><div id="task-status" class="list loading">Loading tasks…</div></div></section>
<section class="two"><div class="panel"><h2>Recent task activity</h2><div id="recent-tasks" class="list loading">Loading tasks…</div></div>
<div class="panel"><h2>Recent company jobs</h2><div id="recent-jobs" class="list loading">Loading jobs…</div></div></section>
<section class="panel wide"><h2>Operating guardrails</h2><span class="status">Human approval for external actions</span><span class="status">No autonomous spending</span><span class="status">No brokerage access</span><span class="status">Private data not shown here</span>
<div class="notice">This HQ shows only persisted records and configuration indicators. It does not claim every role is running, that a client has been delivered, or that revenue has been collected. Messaging, payment reconciliation, and client production releases remain gated until their integrations and evidence are verified.</div></section>
<footer>Session expires after 8 hours. This page does not expose task inputs/outputs, prospect details, approval content, or secrets. Data refreshes every 30 seconds.</footer>
</main>
<script>
const $=id=>document.getElementById(id);
const fmt=v=>String(v??'—');
function row(label,value){const d=document.createElement('div');d.className='item';const a=document.createElement('strong');a.textContent=fmt(label);const b=document.createElement('span');b.textContent=fmt(value);d.append(a,b);return d}
function renderList(id,items,empty){const el=$(id);el.replaceChildren();if(!items||!items.length){el.textContent=empty;el.className='list muted';return}el.className='list';for(const item of items)el.append(row(item.label,item.value))}
async function refresh(){ $('error').hidden=true; $('updated').textContent='Refreshing…';try{const res=await fetch('/hq/api/overview',{credentials:'same-origin',cache:'no-store'});if(res.status===401||res.status===403){location.href='/hq/login';return}if(!res.ok)throw new Error('The HQ status request failed.');const d=await res.json();
$('tasks').textContent=fmt(d.tasks.total);$('jobs').textContent=fmt(d.company_jobs.total);$('approvals').textContent=fmt(d.pending_approvals);$('roles').textContent=fmt(d.agent_roles_defined);
renderList('integrations',[
{label:'Backend API',value:d.backend_status},
{label:'Shared Brain',value:d.shared_brain},
{label:'LLM provider',value:d.model_configured?'configured':'not configured'},
{label:'Email sending',value:d.email_sending?'enabled':'disabled'},
{label:'Data store',value:d.database}
],'No integration status available.');
renderList('task-status',Object.entries(d.tasks.by_status||{}).map(([k,v])=>({label:k,value:v})), 'No tasks recorded yet.');
renderList('recent-tasks',(d.tasks.recent||[]).map(x=>({label:x.kind,value:x.status+' · '+(x.updated_at||x.created_at||'')})),'No task activity recorded yet.');
renderList('recent-jobs',(d.company_jobs.recent||[]).map(x=>({label:x.role,value:x.status+' · '+(x.updated_at||x.created_at||'')})),'No company jobs recorded yet.');
$('updated').textContent='Updated '+new Date(d.generated_at).toLocaleString();
}catch(e){$('error').hidden=false;$('error').textContent='HQ data could not be refreshed. Check the backend health and try again.';$('updated').textContent='Status unavailable';}}
$('refresh').addEventListener('click',refresh);
$('logout').addEventListener('click',async()=>{try{await fetch('/hq/logout',{method:'POST',credentials:'same-origin'});}finally{location.href='/hq/login';}});
refresh();setInterval(refresh,30000);
</script></body></html>"""


@app.get("/hq/login", response_class=HTMLResponse, include_in_schema=False)
def hq_login_page():
    if not _configured():
        return HTMLResponse(
            "<h1>Private HQ is not configured</h1><p>Set HQ_ADMIN_PASSWORD and HQ_SESSION_SECRET on the private backend before enabling owner access.</p>",
            status_code=503, headers=_headers(),
        )
    return HTMLResponse(LOGIN_HTML, headers=_headers())


@app.post("/hq/login", include_in_schema=False)
async def hq_login(request: Request):
    if not _configured():
        raise HTTPException(status_code=503, detail="Private HQ is not configured.")
    body = await request.body()
    if len(body) > MAX_LOGIN_BODY_BYTES:
        raise HTTPException(status_code=413, detail="Login request is too large.")
    fields = parse_qs(body.decode("utf-8", errors="replace"), keep_blank_values=True)
    password = fields.get("password", [""])[0]
    bucket = _login_bucket(request)
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    _ensure_login_attempts_table()
    with db() as conn:
        conn.execute("DELETE FROM hq_login_attempts WHERE attempted_at < ?", (cutoff,))
        attempts = conn.execute(
            "SELECT COUNT(*) AS n FROM hq_login_attempts WHERE ip_hash=? AND attempted_at >= ?",
            (bucket, cutoff),
        ).fetchone()["n"]
    if int(attempts) >= 8:
        return HTMLResponse(
            "<h1>Too many sign-in attempts</h1><p>Wait 15 minutes before trying again.</p>",
            status_code=429, headers={**_headers(), "Retry-After": "900"},
        )
    expected = os.getenv("HQ_ADMIN_PASSWORD", "")
    if not password or not hmac.compare_digest(password.encode(), expected.encode()):
        with db() as conn:
            conn.execute("INSERT INTO hq_login_attempts(ip_hash, attempted_at) VALUES(?, ?)",
                         (bucket, datetime.now(timezone.utc).isoformat()))
        return RedirectResponse("/hq/login?error=1", status_code=303, headers=_headers())
    with db() as conn:
        conn.execute("DELETE FROM hq_login_attempts WHERE ip_hash=?", (bucket,))
    token = _session_token(int(time.time()) + SESSION_TTL_SECONDS)
    response = RedirectResponse("/hq", status_code=303, headers=_headers())
    response.set_cookie(
        COOKIE_NAME, token, max_age=SESSION_TTL_SECONDS, httponly=True,
        secure=True, samesite="strict", path="/hq",
    )
    return response


@app.post("/hq/logout", include_in_schema=False)
def hq_logout():
    response = RedirectResponse("/hq/login", status_code=303, headers=_headers())
    response.delete_cookie(COOKIE_NAME, path="/hq", secure=True, httponly=True, samesite="strict")
    return response


@app.get("/hq", response_class=HTMLResponse, include_in_schema=False)
def hq_page(request: Request):
    if not _valid_session(request.cookies.get(COOKIE_NAME)):
        return RedirectResponse("/hq/login", status_code=303, headers=_headers())
    return HTMLResponse(HQ_HTML, headers=_headers())


@app.get("/hq/api/overview", include_in_schema=False)
def hq_overview(request: Request):
    if not _valid_session(request.cookies.get(COOKIE_NAME)):
        raise HTTPException(status_code=401, detail="Sign in to access the private HQ.")
    with db() as conn:
        task_counts = conn.execute("SELECT status, COUNT(*) AS n FROM tasks GROUP BY status").fetchall()
        job_counts = conn.execute("SELECT status, COUNT(*) AS n FROM company_jobs GROUP BY status").fetchall()
        recent_tasks = conn.execute(
            "SELECT kind, status, created_at, updated_at FROM tasks ORDER BY id DESC LIMIT 8"
        ).fetchall()
        recent_jobs = conn.execute(
            "SELECT role, status, created_at, updated_at FROM company_jobs ORDER BY id DESC LIMIT 8"
        ).fetchall()
        pending = conn.execute("SELECT COUNT(*) AS n FROM approvals WHERE status='pending'").fetchone()["n"]
        task_total = conn.execute("SELECT COUNT(*) AS n FROM tasks").fetchone()["n"]
        job_total = conn.execute("SELECT COUNT(*) AS n FROM company_jobs").fetchone()["n"]
    model_configured = bool(
        (os.getenv("OPENROUTER_API_KEY", "") or os.getenv("LLM_API_KEY", "") or os.getenv("OPENAI_API_KEY", ""))
        and (os.getenv("LLM_MODEL", "") or os.getenv("OPENAI_MODEL", "openrouter/free" if os.getenv("OPENROUTER_API_KEY", "") else "gpt-4.1-mini"))
    )
    return JSONResponse({
        "generated_at": now(),
        "backend_status": "ready",
        "database": "postgresql" if os.getenv("DATABASE_URL", "").strip() else "sqlite",
        "tasks": {
            "total": int(task_total),
            "by_status": {str(row["status"]): int(row["n"]) for row in task_counts},
            "recent": [{"kind": str(row["kind"]), "status": str(row["status"]),
                        "created_at": row["created_at"], "updated_at": row["updated_at"]}
                       for row in recent_tasks],
        },
        "company_jobs": {
            "total": int(job_total),
            "by_status": {str(row["status"]): int(row["n"]) for row in job_counts},
            "recent": [{"role": str(row["role"]), "status": str(row["status"]),
                        "created_at": row["created_at"], "updated_at": row["updated_at"]}
                       for row in recent_jobs],
        },
        "pending_approvals": int(pending),
        "agent_roles_defined": len(AGENT_ROLES),
        "shared_brain": "configured" if SHARED_BRAIN_AGENT_KEY else "not configured",
        "model_configured": model_configured,
        "email_sending": os.getenv("EMAIL_SENDING_ENABLED", "").lower() == "true",
    }, headers=_headers())
