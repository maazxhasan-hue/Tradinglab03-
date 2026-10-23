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
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from pricing_service import (
    PricingValidationError, archive_item, audit_history, create_item,
    list_items, public_items, publish_item, update_item,
)

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
.header-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.navlink{display:inline-block;padding:10px 12px;border-radius:10px;color:#c9d8e8;text-decoration:none;border:1px solid transparent;font-size:.88rem}.navlink:hover,.navlink.active{border-color:#335466;background:#112433;color:var(--teal)}
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
<div class="header-actions"><a class="navlink" href="/hq">Overview</a><a class="navlink active" href="/hq/pricing">Pricing Management</a><button id="refresh">Refresh</button> <button id="logout" class="primary">Sign out</button></div></header>
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


PRICING_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="no-referrer">
<title>Pricing Management · Nexora AI HQ</title>
<style>
:root{color-scheme:dark;font-family:Inter,system-ui,-apple-system,sans-serif;background:#070b12;color:#edf4ff;--panel:#0e1926;--line:#253b50;--muted:#9fb0c5;--teal:#68e8d4;--gold:#f3d99a}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 85% 0%,#123543 0,transparent 36%),#070b12}header{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:18px max(16px,calc((100vw - 1240px)/2));border-bottom:1px solid var(--line);background:#07101bd9}
.brand{font-weight:950;letter-spacing:.12em;color:var(--teal);font-size:.8rem}.sub,.muted{color:var(--muted);font-size:.85rem;margin-top:5px}.header-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
button,a.navlink{cursor:pointer;border:1px solid var(--line);border-radius:10px;padding:10px 12px;color:#edf4ff;background:#111f2e;font:inherit;font-weight:700;text-decoration:none;font-size:.88rem}button.primary{background:var(--teal);color:#071d1b;border-color:var(--teal)}button.danger{border-color:#70414a;color:#ffb7bf}
main{width:min(1240px,calc(100% - 32px));margin:28px auto 60px}.eyebrow{color:var(--teal);font-size:.72rem;letter-spacing:.14em;font-weight:900;text-transform:uppercase}h1{font-size:clamp(2rem,4vw,3.2rem);letter-spacing:-.06em;margin:8px 0}.hero{display:flex;justify-content:space-between;align-items:end;gap:16px;flex-wrap:wrap;margin-bottom:20px}
.layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(320px,.85fr);gap:16px;align-items:start}.panel{border:1px solid var(--line);border-radius:16px;padding:19px;background:linear-gradient(145deg,#112033,var(--panel));min-width:0}.panel h2{font-size:1.05rem;margin:0 0 15px}
.metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-bottom:14px}.metric{padding:13px;border:1px solid var(--line);border-radius:12px;background:#0b1520}.metric span{display:block;color:var(--muted);font-size:.8rem}.metric strong{display:block;font-size:1.5rem;margin-top:6px}
label{display:block;color:#c4d2e1;font-size:.82rem;margin:12px 0 6px}input,select,textarea{width:100%;padding:11px 12px;border:1px solid #344c61;border-radius:10px;background:#07101a;color:#edf4ff;font:inherit;min-width:0}textarea{min-height:82px;resize:vertical}.fields{display:grid;grid-template-columns:1fr 1fr;gap:0 12px}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:15px}.notice{padding:12px 14px;border:1px solid #5b4c2d;border-radius:12px;color:var(--gold);background:#211c11;line-height:1.5;margin:12px 0}.message{padding:11px 13px;border-radius:10px;background:#102c2a;border:1px solid #2b665b;color:var(--teal);margin:12px 0}.message.error{background:#30191e;border-color:#70414a;color:#ffb7bf}.items{display:grid;gap:10px}.price-card{border:1px solid var(--line);border-radius:12px;padding:13px;background:#0a1420}.price-top{display:flex;justify-content:space-between;gap:12px;align-items:start}.price-top strong{display:block;overflow-wrap:anywhere}.price-meta{font-size:.8rem;color:var(--muted);margin-top:5px;line-height:1.5}.amount{font-weight:900;font-size:1.1rem;white-space:nowrap}.pill{display:inline-block;font-size:.72rem;border:1px solid #335466;border-radius:999px;padding:4px 7px;color:var(--teal);margin:8px 5px 0 0}.pill.warning{border-color:#5b4c2d;color:var(--gold)}.price-actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:12px}.price-actions button{font-size:.8rem;padding:8px 10px}.history{font-size:.82rem;line-height:1.5;color:var(--muted);max-height:300px;overflow:auto}.history-item{border-top:1px solid var(--line);padding:9px 0}.empty{color:var(--muted);font-size:.9rem;padding:14px 0}footer{margin-top:18px;color:var(--muted);font-size:.8rem;line-height:1.6}
@media(max-width:850px){.layout{grid-template-columns:1fr}}@media(max-width:520px){.fields{grid-template-columns:1fr}.metrics{grid-template-columns:1fr 1fr 1fr}.metric strong{font-size:1.2rem}.price-top{flex-direction:column}.amount{white-space:normal}}
</style></head><body>
<header><div><div class="brand">NEXORA AI / PRIVATE HQ</div><div class="sub">Pricing control center · Owner-only</div></div>
<div class="header-actions"><a class="navlink" href="/hq">Overview</a><a class="navlink" href="/hq/pricing">Pricing Management</a><button id="reload">Refresh</button><button id="logout" class="primary">Sign out</button></div></header>
<main><section class="hero"><div><div class="eyebrow">Commercial operations</div><h1>Pricing management.</h1><div class="muted">Manage services, subscriptions, and client-specific quotes from one private workspace.</div></div><div id="updated" class="muted">Loading pricing catalog…</div></section>
<div class="notice">Safe publishing: saving changes creates or updates a draft. Customer-facing prices change only after you press Publish. Editing a live price keeps the previous published version active until the new version is published. Client-specific quotes remain private and are never included in the public catalog.</div>
<div id="message" class="message" role="status" aria-live="polite" hidden></div>
<div class="metrics"><div class="metric"><span>Total records</span><strong id="count-all">—</strong></div><div class="metric"><span>Published</span><strong id="count-published">—</strong></div><div class="metric"><span>Draft changes</span><strong id="count-drafts">—</strong></div></div>
<div class="layout"><section class="panel"><h2 id="form-title">Add a pricing item</h2><form id="price-form">
<div class="fields"><div><label for="title">Plan / service name *</label><input id="title" maxlength="120" required placeholder="e.g. AI Automation Starter"></div><div><label for="slug">Public slug *</label><input id="slug" maxlength="100" required pattern="[a-z0-9]+(-[a-z0-9]+)*" placeholder="ai-automation-starter"></div></div>
<div class="fields"><div><label for="category">Category *</label><select id="category" required><option value="service">Service / package</option><option value="subscription">AI agent subscription</option><option value="client_quote">Client-specific quote (private)</option></select></div><div><label for="billing">Billing period *</label><select id="billing" required><option value="one_time">One-time</option><option value="monthly">Monthly</option><option value="yearly">Yearly</option><option value="custom">Custom</option></select></div></div>
<div class="fields"><div><label for="amount">Regular price (₹ INR) *</label><input id="amount" type="number" min="0" max="1000000000" step="0.01" required placeholder="9999.00"></div><div><label for="promo">Promotional price (₹ INR)</label><input id="promo" type="number" min="0" max="1000000000" step="0.01" placeholder="Optional"></div></div>
<div class="fields"><div><label for="discount">Discount percent</label><input id="discount" type="number" min="0" max="100" step="0.01" value="0"></div><div><label for="description">Short description</label><textarea id="description" maxlength="2000" placeholder="What is included?"></textarea></div></div>
<div class="actions"><button class="primary" id="save" type="submit">Save draft</button><button type="button" id="reset">New item</button></div>
</form><div class="muted">Prices are stored as paise-precision integers. Changes are audit-logged; this screen never collects payments or changes existing customer invoices.</div></section>
<div><section class="panel"><h2>Pricing catalog</h2><div id="items" class="items"><div class="empty">Loading items…</div></div></section>
<section class="panel" style="margin-top:14px"><h2>Change history</h2><div id="history" class="history">Choose History on a pricing item to inspect its audit trail.</div></section></div></div>
<footer>Only published service and subscription snapshots appear at the public endpoint <code>/public/pricing</code>. Client-specific quotes are always excluded. Archived items are removed from the public endpoint. Every create, edit, publish, and archive action is recorded.</footer></main>
<script>
const $=id=>document.getElementById(id);let records=[];let editingId=null;let slugTouched=false;
const money=v=>'₹'+Number(v||0).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2});
function showMessage(text,error=false){const el=$('message');el.hidden=false;el.textContent=text;el.className=error?'message error':'message'}
function clearMessage(){$('message').hidden=true;$('message').textContent=''}
function slugify(v){return v.toLowerCase().trim().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,100)}
$('title').addEventListener('input',()=>{if(!slugTouched)$('slug').value=slugify($('title').value)});
$('slug').addEventListener('input',()=>{slugTouched=$('slug').value.length>0});
function resetForm(){editingId=null;slugTouched=false;$('price-form').reset();$('discount').value='0';$('form-title').textContent='Add a pricing item';$('save').textContent='Save draft'}
$('reset').addEventListener('click',()=>{resetForm();clearMessage()});
function setForm(x){editingId=x.id;slugTouched=true;$('title').value=x.title;$('slug').value=x.slug;$('category').value=x.category;$('billing').value=x.billing_period;$('amount').value=x.amount_inr;$('promo').value=x.promo_price_inr??'';$('discount').value=x.discount_percent??'0';$('description').value=x.description||'';$('form-title').textContent='Edit: '+x.title;$('save').textContent='Save draft changes';clearMessage();window.scrollTo({top:0,behavior:'smooth'})}
function button(label,fn,cls=''){const b=document.createElement('button');b.type='button';b.textContent=label;if(cls)b.className=cls;b.addEventListener('click',fn);return b}
async function api(path,options={}){const res=await fetch(path,{credentials:'same-origin',cache:'no-store',...options,headers:{'Content-Type':'application/json',...(options.headers||{})}});if(res.status===401||res.status===403){location.href='/hq/login';throw new Error('Your session expired. Sign in again.')}let data={};try{data=await res.json()}catch{}if(!res.ok)throw new Error(data.detail||'The request could not be completed.');return data}
function renderItems(){const el=$('items');el.replaceChildren();$('count-all').textContent=records.length;$('count-published').textContent=records.filter(x=>x.published).length;$('count-drafts').textContent=records.filter(x=>x.status==='draft'||x.has_unpublished_changes).length;
if(!records.length){const empty=document.createElement('div');empty.className='empty';empty.textContent='No pricing records yet. Add your first item on the left.';el.append(empty);return}
for(const x of records){const card=document.createElement('article');card.className='price-card';const top=document.createElement('div');top.className='price-top';const info=document.createElement('div');const title=document.createElement('strong');title.textContent=x.title;const meta=document.createElement('div');meta.className='price-meta';meta.textContent=x.category.replace('_',' ')+' · '+x.billing_period.replace('_',' ')+' · /'+x.slug;info.append(title,meta);const amount=document.createElement('div');amount.className='amount';amount.textContent=money(x.effective_price_inr??x.amount_inr);top.append(info,amount);card.append(top);if(Number(x.effective_price_inr??x.amount_inr)<Number(x.amount_inr)){const regular=document.createElement('div');regular.className='price-meta';regular.textContent='Regular price: '+money(x.amount_inr);card.append(regular)}
const status=document.createElement('div');const pill=document.createElement('span');pill.className='pill';pill.textContent=x.status==='archived'?'Archived':x.published?'Published':'Draft';status.append(pill);if(x.has_unpublished_changes){const p=document.createElement('span');p.className='pill warning';p.textContent='Unpublished edits';status.append(p)}if(x.promo_price_inr!==null){const p=document.createElement('span');p.className='pill';p.textContent='Promo '+money(x.promo_price_inr);status.append(p)}if(Number(x.discount_percent)>0){const p=document.createElement('span');p.className='pill';p.textContent=x.discount_percent+'% off';status.append(p)}card.append(status);
if(x.description){const desc=document.createElement('div');desc.className='price-meta';desc.textContent=x.description;card.append(desc)}
const actions=document.createElement('div');actions.className='price-actions';if(x.status!=='archived')actions.append(button('Edit',()=>setForm(x)));
if(x.status!=='archived')actions.append(button(x.category==='client_quote'?(x.published?'Save approved snapshot':'Finalize quote'):(x.published?'Publish updates':'Publish'),async()=>{if(!confirm(x.category==='client_quote'?'Finalize this private client quote inside HQ?':'Publish '+x.title+' to the public pricing endpoint?'))return;try{await api('/hq/api/pricing/'+x.id+'/publish',{method:'POST',body:'{}'});showMessage('Published '+x.title+'.');await loadItems()}catch(e){showMessage(e.message,true)}} ,'primary'));
if(x.status!=='archived')actions.append(button('Archive',async()=>{if(!confirm('Archive '+x.title+' and remove it from public pricing?'))return;try{await api('/hq/api/pricing/'+x.id+'/archive',{method:'POST',body:'{}'});showMessage('Archived '+x.title+'.');await loadItems()}catch(e){showMessage(e.message,true)}} ,'danger'));
actions.append(button('History',async()=>{try{const h=await api('/hq/api/pricing/'+x.id+'/history');renderHistory(h.items)}catch(e){showMessage(e.message,true)}}));card.append(actions);el.append(card)}}
function renderHistory(items){const el=$('history');el.replaceChildren();if(!items.length){el.textContent='No history recorded yet.';return}for(const x of items){const d=document.createElement('div');d.className='history-item';const strong=document.createElement('strong');strong.textContent=x.event.replaceAll('_',' ');const meta=document.createElement('div');meta.textContent=x.created_at+' · '+x.actor;const detail=document.createElement('div');const snap=x.after||{};detail.textContent=snap.title?('After: '+snap.title+' · '+money(Number(snap.amount_paise||0)/100)):'No after snapshot';d.append(strong,meta,detail);el.append(d)}}
async function loadItems(){try{const d=await api('/hq/api/pricing?include_archived=true');records=d.items||[];renderItems();$('updated').textContent='Updated '+new Date().toLocaleString()}catch(e){$('items').textContent=e.message;showMessage(e.message,true);$('updated').textContent='Unavailable'}}
$('price-form').addEventListener('submit',async e=>{e.preventDefault();clearMessage();const payload={title:$('title').value,slug:$('slug').value,category:$('category').value,billing_period:$('billing').value,amount_inr:$('amount').value,promo_price_inr:$('promo').value===''?null:$('promo').value,discount_percent:$('discount').value||'0',description:$('description').value};$('save').disabled=true;try{await api(editingId?'/hq/api/pricing/'+editingId:'/hq/api/pricing',{method:editingId?'PUT':'POST',body:JSON.stringify(payload)});showMessage(editingId?'Draft changes saved. The previous public price remains live until you publish.':'Draft saved. Publish it when you are ready.');resetForm();await loadItems()}catch(err){showMessage(err.message,true)}finally{$('save').disabled=false}});
$('reload').addEventListener('click',loadItems);$('logout').addEventListener('click',async()=>{try{await fetch('/hq/logout',{method:'POST',credentials:'same-origin'})}finally{location.href='/hq/login'}});loadItems();
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


class PricingPayload(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=100)
    category: str
    description: str = Field(default="", max_length=2000)
    amount_inr: Decimal
    billing_period: str = "one_time"
    discount_percent: Decimal = Decimal("0")
    promo_price_inr: Optional[Decimal] = None


def _require_hq_owner(request: Request) -> None:
    if not _valid_session(request.cookies.get(COOKIE_NAME)):
        raise HTTPException(status_code=401, detail="Sign in to access pricing management.")


@app.get("/hq/pricing", response_class=HTMLResponse, include_in_schema=False)
def hq_pricing_page(request: Request):
    if not _valid_session(request.cookies.get(COOKIE_NAME)):
        return RedirectResponse("/hq/login", status_code=303, headers=_headers())
    return HTMLResponse(PRICING_HTML, headers=_headers())


@app.get("/hq/api/pricing", include_in_schema=False)
def hq_list_pricing(request: Request, include_archived: bool = False):
    _require_hq_owner(request)
    return JSONResponse({"items": list_items(include_archived=include_archived)}, headers=_headers())


@app.post("/hq/api/pricing", status_code=201, include_in_schema=False)
def hq_create_pricing(payload: PricingPayload, request: Request):
    _require_hq_owner(request)
    try:
        item = create_item(payload.dict(), actor="owner")
        return JSONResponse(item, status_code=201, headers=_headers())
    except PricingValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


@app.put("/hq/api/pricing/{item_id}", include_in_schema=False)
def hq_update_pricing(item_id: int, payload: PricingPayload, request: Request):
    _require_hq_owner(request)
    try:
        return JSONResponse(update_item(item_id, payload.dict(), actor="owner"), headers=_headers())
    except KeyError:
        raise HTTPException(status_code=404, detail="Pricing item not found.") from None
    except PricingValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


@app.post("/hq/api/pricing/{item_id}/publish", include_in_schema=False)
def hq_publish_pricing(item_id: int, request: Request):
    _require_hq_owner(request)
    try:
        return JSONResponse(publish_item(item_id, actor="owner"), headers=_headers())
    except KeyError:
        raise HTTPException(status_code=404, detail="Pricing item not found.") from None
    except PricingValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


@app.post("/hq/api/pricing/{item_id}/archive", include_in_schema=False)
def hq_archive_pricing(item_id: int, request: Request):
    _require_hq_owner(request)
    try:
        return JSONResponse(archive_item(item_id, actor="owner"), headers=_headers())
    except KeyError:
        raise HTTPException(status_code=404, detail="Pricing item not found.") from None


@app.get("/hq/api/pricing/{item_id}/history", include_in_schema=False)
def hq_pricing_history(item_id: int, request: Request):
    _require_hq_owner(request)
    items = list_items(include_archived=True)
    if not any(item["id"] == item_id for item in items):
        raise HTTPException(status_code=404, detail="Pricing item not found.")
    return JSONResponse({"items": audit_history(item_id)}, headers=_headers())


@app.get("/public/pricing", include_in_schema=False)
def public_pricing_catalog():
    # Only explicitly published snapshots are returned; drafts and audit records stay private.
    return JSONResponse(
        {"items": public_items()},
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
