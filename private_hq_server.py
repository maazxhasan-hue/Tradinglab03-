#!/usr/bin/env python3
"""Small authenticated gateway for the private Nexora HQ on Render."""
from __future__ import annotations

import hashlib
import hmac
import html
import json
import sys
import http.cookies
import os
import secrets
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent / "private-hq"
APP_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_ROOT))
from company.nexora_growth_runtime import AGENT_DIRECTORY, AGENTS, COMPANY_AGENTS, GrowthStore
from company.nexora_agent_executor import execute_agent_draft, DraftExecutionError, ProviderNotConfigured, provider_status, brain_status
from company.nexora_batch_executor import start_all_agents, start_company_workforce, batch_status, resume_queued_tasks
from company.role_contracts import all_role_contracts, role_contract
from company.production_health import check_shared_brain
from company.service_pricing import PricingStore, PricingValidationError
from company.observability import build_monitoring_snapshot
from company.database import database_target, is_postgres_target, connect_database
PRICING_DB = os.environ.get("NEXORA_PRICING_DB", str(APP_ROOT / "data" / "nexora_pricing.sqlite3"))
GROWTH_DB = os.environ.get("NEXORA_GROWTH_DB", str(APP_ROOT / "data" / "nexora_growth.sqlite3"))
GROWTH_ENABLED = os.environ.get("NEXORA_GROWTH_ENABLED", "false").lower() == "true"
PASSWORD = os.environ.get("HQ_ACCESS_PASSWORD", "") or os.environ.get("HQ_ADMIN_PASSWORD", "")
SESSION_SECRET = os.environ.get("HQ_SESSION_SECRET", "")
PORT = int(os.environ.get("PORT", "10000"))
SESSION_TTL = 8 * 60 * 60
# Serve only reviewed HQ documents and the local analytics asset they reference.
# Everything in this allowlist is still protected by the authenticated session gate.
ALLOWED = {
    "index.html",
    "company-workforce.html",
    "agent-town.html",
    "harvey.html",
    "inbox.html",
    "video-agent.html",
    "creative-agent.html",
    "marketing.html",
    "growth-hq.html",
    "visitor-analytics.html",
    "visitor-analytics-ui.js",
    "pricing-admin.html",
    "monitoring.html",
}
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".json": "application/json; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}


def content_type_for(name: str) -> str:
    """Return the MIME type for a specifically allowlisted HQ file."""
    return CONTENT_TYPES.get(Path(name).suffix.lower(), "application/octet-stream")


def storage_readiness() -> dict:
    """Describe whether both production stores use durable PostgreSQL, without exposing URLs."""
    growth_target = database_target(GROWTH_DB)
    pricing_target = database_target(PRICING_DB)
    growth_backend = "postgres" if is_postgres_target(growth_target) else "sqlite"
    pricing_backend = "postgres" if is_postgres_target(pricing_target) else "sqlite"
    persistent = growth_backend == "postgres" and pricing_backend == "postgres"
    backend = "postgres" if persistent else ("sqlite" if growth_backend == pricing_backend else "mixed")
    return {
        "backend": backend,
        "persistent": persistent,
        "growth_backend": growth_backend,
        "pricing_backend": pricing_backend,
    }


def check_persistent_storage() -> tuple[bool, dict]:
    """Require reachable PostgreSQL before production writes or agent execution."""
    status = storage_readiness()
    if not status["persistent"]:
        status["connection"] = "not_checked"
        return False, status
    try:
        for target in (database_target(GROWTH_DB), database_target(PRICING_DB)):
            with connect_database(target, timeout=5) as db:
                db.execute("SELECT 1").fetchone()
        status["connection"] = "ok"
        return True, status
    except Exception as exc:
        status["connection"] = "failed"
        status["error_type"] = type(exc).__name__
        return False, status
LOGIN_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Nexora HQ · Sign in</title><style>*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:#080d16;color:#edf4ff;font:16px/1.5 system-ui,sans-serif;padding:20px}.card{width:min(420px,100%);padding:30px;background:#101a29;border:1px solid #24344a;box-shadow:8px 8px #030811}.brand{color:#54e7d2;font-weight:900;letter-spacing:.14em;font-size:.75rem}h1{font-size:1.7rem}p{color:#9aabc1}label{display:block;margin:18px 0 7px}input{width:100%;padding:13px;background:#080d16;border:1px solid #31465e;color:#edf4ff;border-radius:4px}button{width:100%;margin-top:16px;padding:13px;background:#54e7d2;border:0;color:#06121a;font-weight:900;cursor:pointer}small{display:block;margin-top:16px;color:#9aabc1}</style></head><body><main class="card"><div class="brand">NEXORA AI / PRIVATE WORKSPACE</div><h1>Company HQ</h1><p>Sign in to access the internal workspace.</p><form method="post" action="/login"><label for="password">Access password</label><input id="password" name="password" type="password" autocomplete="current-password" required autofocus><button type="submit">SIGN IN</button></form><small>Protected session · Sign-in expires after 8 hours.</small></main></body></html>"""

def b64(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def make_token() -> str:
    expiry = str(int(time.time()) + SESSION_TTL)
    nonce = secrets.token_urlsafe(16)
    payload = f"{expiry}.{nonce}"
    sig = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return b64(f"{payload}.{sig}".encode())

def valid_token(token: str) -> bool:
    import base64
    try:
        raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4)).decode()
        expiry, nonce, signature = raw.split(".", 2)
        if int(expiry) < int(time.time()) or int(expiry) > int(time.time()) + SESSION_TTL + 60:
            return False
        payload = f"{expiry}.{nonce}"
        expected = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)
    except (ValueError, UnicodeError):
        return False

class Handler(BaseHTTPRequestHandler):
    server_version = "NexoraHQGateway"

    def do_HEAD(self):
        """Support platform health probes without returning response bodies."""
        parsed = urlparse(self.path)
        if parsed.path == "/healthz":
            self.send_headers(200, "application/json; charset=utf-8")
            return
        if parsed.path == "/":
            self.send_headers(200, "text/html; charset=utf-8")
            return
        self.send_headers(404, "text/plain; charset=utf-8")
    def log_message(self, fmt, *args):
        # Never log credentials, request bodies, or cookie headers.
        super().log_message(fmt, *args)

    def send_headers(self, status=200, content_type="text/html; charset=utf-8", extra=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store, private, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        if extra:
            for k, v in extra:
                self.send_header(k, v)
        self.end_headers()

    def body(self, status, content, content_type="text/html; charset=utf-8", extra=None):
        data = content if isinstance(content, bytes) else content.encode()
        self.send_headers(status, content_type, extra)
        self.wfile.write(data)

    def authenticated(self):
        cookie = http.cookies.SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
            morsel = cookie.get("nexora_hq_session")
            return bool(morsel and valid_token(morsel.value))
        except Exception:
            return False

    def require_persistent_storage(self) -> bool:
        ready, status = check_persistent_storage()
        if ready:
            return True
        self.body(503, json.dumps({
            "error": "persistent_storage_not_ready",
            "message": "Writes and agent execution are locked until both HQ stores use reachable PostgreSQL. SQLite on a free Render instance can be lost on restart.",
            "storage": status,
        }), "application/json; charset=utf-8")
        return False

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/pricing/"):
            if not self.authenticated():
                self.body(401, json.dumps({"error":"authentication_required"}), "application/json; charset=utf-8"); return
            if parsed.path == "/api/pricing/services":
                self.body(200, json.dumps({"currency":"INR","max_price":499,"services":PricingStore(PRICING_DB).list_services()}), "application/json; charset=utf-8"); return
            self.body(404, json.dumps({"error":"not_found"}), "application/json; charset=utf-8"); return
        if parsed.path.startswith("/api/company/"):
            if not self.authenticated():
                self.body(401, json.dumps({"error":"authentication_required"}), "application/json; charset=utf-8"); return
            store = GrowthStore(GROWTH_DB)
            if parsed.path == "/api/company/role-contracts":
                contracts = all_role_contracts()
                self.body(200, json.dumps({"contract_count": len(contracts), "contracts": contracts}), "application/json; charset=utf-8"); return
            if parsed.path.startswith("/api/company/role-contracts/"):
                agent_id = parsed.path.removeprefix("/api/company/role-contracts/")
                try:
                    contract = role_contract(agent_id)
                except KeyError:
                    self.body(404, json.dumps({"error":"unknown_agent"}), "application/json; charset=utf-8"); return
                self.body(200, json.dumps({"contract": contract}), "application/json; charset=utf-8"); return
            if parsed.path == "/api/company/brain-check":
                self.body(200, json.dumps(check_shared_brain()), "application/json; charset=utf-8"); return
            if parsed.path == "/api/company/agents":
                roster = sorted(AGENT_DIRECTORY.values(), key=lambda agent: (agent["department"], agent["name"]))
                self.body(200, json.dumps({
                    "roles_defined": len(roster),
                    "company_roles": len(COMPANY_AGENTS),
                    "growth_roles": len(AGENTS),
                    "roles": roster,
                    "ai_provider": provider_status(),
                    "brain": brain_status(),
                    "storage": storage_readiness(),
                    "batch": batch_status(),
                }), "application/json; charset=utf-8"); return
            if parsed.path == "/api/company/batch":
                self.body(200, json.dumps(batch_status()), "application/json; charset=utf-8"); return
            if parsed.path == "/api/company/monitoring":
                snapshot = build_monitoring_snapshot(store, limit=250)
                self.body(200, json.dumps(snapshot), "application/json; charset=utf-8"); return
            if parsed.path == "/api/company/tasks":
                self.body(200, json.dumps({"tasks": store.list_tasks(limit=250)}), "application/json; charset=utf-8"); return
            self.body(404, json.dumps({"error":"not_found"}), "application/json; charset=utf-8"); return
        if parsed.path.startswith("/api/company/"):
            if not self.authenticated():
                self.body(401, json.dumps({"error":"authentication_required"}), "application/json; charset=utf-8"); return
            self.body(403, json.dumps({"error":"action_not_available"}), "application/json; charset=utf-8"); return
        if parsed.path.startswith("/api/growth/"):
            if not self.authenticated():
                self.body(401, json.dumps({"error":"authentication_required"}), "application/json; charset=utf-8"); return
            if parsed.path == "/api/growth/overview":
                self.body(200, json.dumps(GrowthStore(GROWTH_DB).overview()), "application/json; charset=utf-8"); return
            if parsed.path == "/api/growth/agents":
                self.body(200, json.dumps({"agents":AGENTS,"execution_enabled":GROWTH_ENABLED,"ai_provider":provider_status(),"brain":brain_status()}), "application/json; charset=utf-8"); return
            if parsed.path == "/api/growth/tasks":
                self.body(200, json.dumps({"tasks":GrowthStore(GROWTH_DB).list_tasks()}), "application/json; charset=utf-8"); return
            if parsed.path == "/api/growth/batch":
                self.body(200, json.dumps(batch_status()), "application/json; charset=utf-8"); return
            self.body(404, json.dumps({"error":"not_found"}), "application/json; charset=utf-8"); return
        path = parsed.path
        if path == "/healthz":
            # Safe, credential-free readiness check: never return or log the database URL.
            try:
                growth_target = database_target(GROWTH_DB)
                pricing_target = database_target(PRICING_DB)
                with connect_database(growth_target, timeout=5) as db:
                    db.execute("SELECT 1").fetchone()
                with connect_database(pricing_target, timeout=5) as db:
                    db.execute("SELECT 1").fetchone()
                storage = storage_readiness()
                payload = {
                    "status": "ok",
                    "database": storage["backend"],
                    "database_connection": "ok",
                    "persistent_storage": storage["persistent"],
                }
                self.body(200, json.dumps(payload), "application/json; charset=utf-8")
            except Exception as exc:
                self.body(503, json.dumps({
                    "status": "degraded",
                    "database_connection": "failed",
                    "error_type": type(exc).__name__,
                }), "application/json; charset=utf-8")
            return
        if path in ("/", "/login"):
            if self.authenticated():
                self.send_response(303); self.send_header("Location", "/index.html"); self.send_header("Cache-Control", "no-store"); self.end_headers()
            else:
                self.body(200, LOGIN_HTML)
            return
        if path == "/logout":
            self.body(200, LOGIN_HTML, extra=[("Set-Cookie", "nexora_hq_session=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Strict")])
            return
        name = path.lstrip("/")
        if name not in ALLOWED:
            self.body(404, "Not found"); return
        if not self.authenticated():
            self.send_response(303); self.send_header("Location", "/login"); self.send_header("Cache-Control", "no-store"); self.end_headers(); return
        try:
            content = (ROOT / name).read_bytes()
        except OSError:
            self.body(503, "HQ page is temporarily unavailable"); return
        self.body(200, content, content_type_for(name))

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/pricing/"):
            if not self.authenticated():
                self.body(401, json.dumps({"error":"authentication_required"}), "application/json; charset=utf-8"); return
            if parsed.path == "/api/pricing/services/update" and not self.require_persistent_storage(): return
            if parsed.path != "/api/pricing/services/update":
                self.body(404, json.dumps({"error":"not_found"}), "application/json; charset=utf-8"); return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 8192:
                    raise ValueError("Request body must be 1-8192 bytes.")
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("Request body must be a JSON object.")
                result = PricingStore(PRICING_DB).update_service(str(data.get("service_id", "")), data.get("price"))
                self.body(200, json.dumps({"ok": True, "service": result, "max_price": 499}), "application/json; charset=utf-8"); return
            except PricingValidationError as exc:
                self.body(400, json.dumps({"error":"invalid_price","message":str(exc)}), "application/json; charset=utf-8"); return
            except (ValueError, json.JSONDecodeError) as exc:
                self.body(400, json.dumps({"error":str(exc)}), "application/json; charset=utf-8"); return
            except KeyError:
                self.body(404, json.dumps({"error":"service_not_found"}), "application/json; charset=utf-8"); return
            except Exception:
                self.body(500, json.dumps({"error":"pricing_update_failed"}), "application/json; charset=utf-8"); return
        if parsed.path == "/api/company/agents/start-all":
            if not self.authenticated():
                self.body(401, json.dumps({"error":"authentication_required"}), "application/json; charset=utf-8"); return
            if not self.require_persistent_storage(): return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 8192:
                    raise ValueError("Request body must be 1-8192 bytes.")
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("Request body must be a JSON object.")
                mission = str(data.get("mission", "")).strip()
                if len(mission) < 10 or len(mission) > 4000:
                    raise ValueError("Mission must be 10-4000 characters.")
                result = start_company_workforce(GrowthStore(GROWTH_DB), mission)
                status = 202 if result.get("started") else 409
                self.body(status, json.dumps(result), "application/json; charset=utf-8"); return
            except ProviderNotConfigured as exc:
                self.body(503, json.dumps({"error":"provider_not_configured","message":str(exc)}),
                          "application/json; charset=utf-8"); return
            except (ValueError, json.JSONDecodeError) as exc:
                self.body(400, json.dumps({"error":str(exc)}), "application/json; charset=utf-8"); return
            except Exception as exc:
                self.body(500, json.dumps({"error":"company_workforce_start_failed",
                                           "detail":type(exc).__name__}), "application/json; charset=utf-8"); return
        if parsed.path.startswith("/api/growth/"):
            if not self.authenticated():
                self.body(401, json.dumps({"error":"authentication_required"}), "application/json; charset=utf-8"); return
            if parsed.path == "/api/growth/agents/start-all":
                if not self.require_persistent_storage(): return
                try:
                    result = start_all_agents(GrowthStore(GROWTH_DB))
                    status = 202 if result.get("started") else 409
                    self.body(status, json.dumps(result), "application/json; charset=utf-8"); return
                except ProviderNotConfigured as exc:
                    self.body(503, json.dumps({"error":"provider_not_configured","message":str(exc)}),
                        "application/json; charset=utf-8"); return
                except Exception:
                    self.body(500, json.dumps({"error":"batch_start_failed"}), "application/json; charset=utf-8"); return
            if parsed.path.startswith("/api/growth/tasks/") and parsed.path.endswith("/run"):
                task_id = parsed.path[len("/api/growth/tasks/"):-len("/run")].strip("/")
                if not task_id or "/" in task_id:
                    self.body(400, json.dumps({"error":"invalid_task_id"}), "application/json; charset=utf-8"); return
                if not self.require_persistent_storage(): return
                try:
                    task = execute_agent_draft(GrowthStore(GROWTH_DB), task_id)
                    self.body(200, json.dumps({"task_id":task["task_id"],"status":task["status"],
                        "outputs":task["outputs"],"execution_started":True,"mode":"draft_only"}),
                        "application/json; charset=utf-8"); return
                except ProviderNotConfigured as exc:
                    self.body(503, json.dumps({"error":"provider_not_configured","message":str(exc)}),
                        "application/json; charset=utf-8"); return
                except KeyError:
                    self.body(404, json.dumps({"error":"task_not_found"}), "application/json; charset=utf-8"); return
                except DraftExecutionError as exc:
                    self.body(409, json.dumps({"error":"draft_execution_failed","message":str(exc)}),
                        "application/json; charset=utf-8"); return
            if parsed.path != "/api/growth/tasks":
                self.body(403, json.dumps({"error":"action_not_available"}), "application/json; charset=utf-8"); return
            if not self.require_persistent_storage(): return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 8192: raise ValueError("invalid_body_size")
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                title, agent_id = str(data.get("title", "")), str(data.get("agent_id", ""))
                context = str(data.get("context", ""))
                if len(context) > 3000: raise ValueError("context_too_long")
                task = GrowthStore(GROWTH_DB).create_task(title, agent_id, {"context":context,"mode":"draft_only"})
                self.body(201, json.dumps({"task_id":task["task_id"],"status":task["status"],"execution_started":False}), "application/json; charset=utf-8"); return
            except (ValueError, KeyError, json.JSONDecodeError) as exc:
                self.body(400, json.dumps({"error":str(exc)}), "application/json; charset=utf-8"); return
            except Exception:
                self.body(500, json.dumps({"error":"internal_error"}), "application/json; charset=utf-8"); return
        if parsed.path != "/login":
            self.body(404, "Not found"); return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > 4096:
            self.body(400, LOGIN_HTML); return
        raw = self.rfile.read(length).decode("utf-8", "replace")
        supplied = parse_qs(raw).get("password", [""])[0]
        if not PASSWORD or not SESSION_SECRET or not hmac.compare_digest(supplied, PASSWORD):
            time.sleep(0.4)
            self.body(401, LOGIN_HTML); return
        token = make_token()
        self.send_response(303)
        self.send_header("Location", "/index.html")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Set-Cookie", f"nexora_hq_session={token}; Path=/; Max-Age={SESSION_TTL}; HttpOnly; Secure; SameSite=Strict")
        self.end_headers()

if __name__ == "__main__":
    if len(PASSWORD) < 16 or len(SESSION_SECRET) < 32:
        raise SystemExit("HQ_ACCESS_PASSWORD/HQ_ADMIN_PASSWORD must be at least 16 chars and HQ_SESSION_SECRET at least 32 chars.")
    # Emit a sanitized startup readiness record so operators can verify the selected backend.
    try:
        growth_target = database_target(GROWTH_DB)
        pricing_target = database_target(PRICING_DB)
        growth_store = GrowthStore(GROWTH_DB)
        pricing_store = PricingStore(PRICING_DB)
        with connect_database(growth_target, timeout=5) as db:
            db.execute("SELECT 1").fetchone()
        with connect_database(pricing_target, timeout=5) as db:
            db.execute("SELECT 1").fetchone()
        print(json.dumps({
            "event": "database_readiness",
            "status": "ok",
            "backend": storage_readiness()["backend"],
            "persistent_storage": storage_readiness()["persistent"],
            "task_records_readable": len(growth_store.list_tasks(limit=1)),
            "pricing_services_readable": len(pricing_store.list_services()),
            "ai_provider": provider_status(),
            "shared_brain": brain_status(),
            "growth_execution_enabled": GROWTH_ENABLED,
        }), flush=True)
    except Exception as exc:
        print(json.dumps({
            "event": "database_readiness",
            "status": "failed",
            "error_type": type(exc).__name__,
        }), flush=True)
    # Recover any durable queued drafts after a process restart; no new tasks are fabricated.
    try:
        recovered = resume_queued_tasks(GrowthStore(GROWTH_DB))
        if recovered.get("started"):
            print(json.dumps({"event": "queued_task_recovery_started", "queued": recovered.get("queued", 0)}))
    except Exception as exc:
        print(json.dumps({"event": "queued_task_recovery_failed", "error_type": type(exc).__name__}))
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
