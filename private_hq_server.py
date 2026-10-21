#!/usr/bin/env python3
"""Small authenticated gateway for the private Nexora HQ on Render."""
from __future__ import annotations

import hashlib
import hmac
import html
import http.cookies
import os
import secrets
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent / "private-hq"
PASSWORD = os.environ.get("HQ_ACCESS_PASSWORD", "")
SESSION_SECRET = os.environ.get("HQ_SESSION_SECRET", "")
PORT = int(os.environ.get("PORT", "10000"))
SESSION_TTL = 8 * 60 * 60
# Serve only reviewed HQ documents and the local analytics asset they reference.
# Everything in this allowlist is still protected by the authenticated session gate.
ALLOWED = {
    "index.html",
    "agent-town.html",
    "harvey.html",
    "inbox.html",
    "marketing.html",
    "visitor-analytics.html",
    "visitor-analytics-ui.js",
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

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/healthz":
            self.body(200, '{"status":"ok"}', "application/json; charset=utf-8")
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
        if urlparse(self.path).path != "/login":
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
        raise SystemExit("HQ_ACCESS_PASSWORD must be at least 16 chars and HQ_SESSION_SECRET at least 32 chars.")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
