"""Harvey worker API: persistent prospect queue, safe discovery, approval-gated outreach.
No email is sent by this service. Outreach remains a draft until a separate, explicitly
configured mail provider and approval flow are implemented.
"""
from __future__ import annotations
import os, sqlite3, secrets
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx

APP_NAME = "Nexora Harvey Worker"
DB_PATH = os.getenv("DATABASE_PATH", "harvey.db")
API_KEY = os.getenv("HARVEY_API_KEY", "")
app = FastAPI(title=APP_NAME, version="0.1.0")
ALLOWED_ORIGINS = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "https://nexora-ai-sooty-two.vercel.app,https://nexora-ai.vercel.app").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=False, allow_methods=["GET","POST","OPTIONS"], allow_headers=["Content-Type","X-API-Key"])

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def db():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS prospects(
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category TEXT,
          website TEXT, phone TEXT, city TEXT NOT NULL, source TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'new', notes TEXT, created_at TEXT NOT NULL,
          UNIQUE(name, city))""")
        c.execute("""CREATE TABLE IF NOT EXISTS tasks(
          id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, status TEXT NOT NULL,
          input_json TEXT NOT NULL, output_json TEXT, error TEXT, created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS approvals(
          id INTEGER PRIMARY KEY AUTOINCREMENT, prospect_id INTEGER, kind TEXT NOT NULL,
          content TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
          created_at TEXT NOT NULL, decided_at TEXT,
          FOREIGN KEY(prospect_id) REFERENCES prospects(id))""")
        c.execute("CREATE INDEX IF NOT EXISTS ix_tasks_status ON tasks(status)")
        c.execute("CREATE INDEX IF NOT EXISTS ix_approvals_status ON approvals(status)")
init_db()

def require_key(x_api_key: Optional[str]):
    if not API_KEY:
        raise HTTPException(503, "Worker is not configured: set HARVEY_API_KEY before use.")
    if not x_api_key or not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(401, "Invalid or missing X-API-Key.")

class DiscoverRequest(BaseModel):
    city: str = Field(min_length=2, max_length=100)
    category: str = Field(default="business", min_length=2, max_length=80)
    limit: int = Field(default=15, ge=1, le=50)

class DraftRequest(BaseModel):
    prospect_id: int
    service: str = Field(min_length=2, max_length=200)
    value_proposition: str = Field(min_length=10, max_length=1000)

class DecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")

@app.get("/health")
def health():
    with db() as c:
        prospects = c.execute("SELECT COUNT(*) n FROM prospects").fetchone()["n"]
        pending = c.execute("SELECT COUNT(*) n FROM approvals WHERE status='pending'").fetchone()["n"]
        tasks = c.execute("SELECT COUNT(*) n FROM tasks").fetchone()["n"]
    return {"service": APP_NAME, "status": "ready", "time": now(),
            "database": "connected", "prospects": prospects, "pending_approvals": pending,
            "tasks_recorded": tasks, "email_sending": "disabled"}

@app.get("/metrics")
def metrics(x_api_key: Optional[str] = Header(default=None)):
    require_key(x_api_key)
    with db() as c:
        return {
          "prospects": c.execute("SELECT COUNT(*) n FROM prospects").fetchone()["n"],
          "new_prospects": c.execute("SELECT COUNT(*) n FROM prospects WHERE status='new'").fetchone()["n"],
          "pending_approvals": c.execute("SELECT COUNT(*) n FROM approvals WHERE status='pending'").fetchone()["n"],
          "approved": c.execute("SELECT COUNT(*) n FROM approvals WHERE status='approved'").fetchone()["n"],
          "tasks": c.execute("SELECT COUNT(*) n FROM tasks").fetchone()["n"]
        }

@app.post("/prospects/discover")
async def discover(req: DiscoverRequest, x_api_key: Optional[str] = Header(default=None)):
    require_key(x_api_key)
    # Public OpenStreetMap Overpass endpoint. Rate-limit requests and store only business listing data.
    task_input = __import__("json").dumps(req.model_dump())
    with db() as c:
        task_id = c.execute("INSERT INTO tasks(kind,status,input_json,created_at,updated_at) VALUES(?,?,?,?,?)",
                            ("discover", "running", task_input, now(), now())).lastrowid
    query = f'''[out:json][timeout:25];area["name"="{req.city}"]["boundary"="administrative"]->.a;
      (node["name"]["shop"](area.a);way["name"]["shop"](area.a);node["name"]["office"](area.a);
       way["name"]["office"](area.a);node["name"]["amenity"~"^(restaurant|cafe|clinic|bank|school)$"](area.a);
       way["name"]["amenity"~"^(restaurant|cafe|clinic|bank|school)$"](area.a););out center tags {req.limit};'''
    try:
        async with httpx.AsyncClient(timeout=35, headers={"User-Agent":"NexoraHarvey/0.1 (business prospect research)"}) as client:
            response = await client.post("https://overpass-api.de/api/interpreter", data={"data": query})
            response.raise_for_status()
            data = response.json()
        found = []
        with db() as c:
            for el in data.get("elements", []):
                tags = el.get("tags", {})
                name = tags.get("name")
                if not name: continue
                website = tags.get("website") or tags.get("contact:website")
                phone = tags.get("phone") or tags.get("contact:phone")
                cat = tags.get("shop") or tags.get("office") or tags.get("amenity") or req.category
                cur = c.execute("""INSERT OR IGNORE INTO prospects(name,category,website,phone,city,source,status,created_at)
                                   VALUES(?,?,?,?,?,'OpenStreetMap','new',?)""",
                                (name, cat, website, phone, req.city, now()))
                row = c.execute("SELECT id,name,category,website,phone,city,status FROM prospects WHERE name=? AND city=?",
                                (name, req.city)).fetchone()
                if row: found.append(dict(row))
            c.execute("UPDATE tasks SET status='completed',output_json=?,updated_at=? WHERE id=?",
                      (__import__("json").dumps({"found":len(found)}), now(), task_id))
        return {"task_id": task_id, "status": "completed", "count": len(found), "prospects": found[:req.limit],
                "source": "OpenStreetMap", "note": "Listings can be incomplete. Verify each business before outreach."}
    except Exception as e:
        with db() as c:
            c.execute("UPDATE tasks SET status='failed',error=?,updated_at=? WHERE id=?",
                      (str(e)[:500], now(), task_id))
        raise HTTPException(502, f"Prospect discovery failed; task {task_id} recorded. Retry later.")

@app.get("/prospects")
def list_prospects(limit: int = 50, x_api_key: Optional[str] = Header(default=None)):
    require_key(x_api_key)
    with db() as c:
        rows = c.execute("SELECT * FROM prospects ORDER BY id DESC LIMIT ?", (max(1,min(limit,200)),)).fetchall()
    return {"items":[dict(r) for r in rows]}

@app.post("/outreach/draft")
def create_draft(req: DraftRequest, x_api_key: Optional[str] = Header(default=None)):
    require_key(x_api_key)
    with db() as c:
        prospect = c.execute("SELECT * FROM prospects WHERE id=?", (req.prospect_id,)).fetchone()
        if not prospect: raise HTTPException(404, "Prospect not found.")
        name = prospect["name"]
        content = (f"Subject: A quick idea for {name}\n\n"
                   f"Hi {name} team,\n\nI came across your business while researching local companies. "
                   f"We help with {req.service}. {req.value_proposition}\n\n"
                   "Would you be open to a short conversation to see whether this could be useful?\n\n"
                   "Best,\nNexora")
        approval_id = c.execute("INSERT INTO approvals(prospect_id,kind,content,status,created_at) VALUES(?,?,?,?,?)",
                                (req.prospect_id, "email_draft", content, "pending", now())).lastrowid
    return {"approval_id": approval_id, "status": "pending", "content": content,
            "message": "Draft saved for human review. No message has been sent."}

@app.get("/approvals")
def list_approvals(x_api_key: Optional[str] = Header(default=None)):
    require_key(x_api_key)
    with db() as c:
        rows = c.execute("""SELECT a.*,p.name prospect_name,p.city FROM approvals a
                            LEFT JOIN prospects p ON p.id=a.prospect_id ORDER BY a.id DESC LIMIT 100""").fetchall()
    return {"items":[dict(r) for r in rows]}

@app.post("/approvals/{approval_id}/decision")
def decide(approval_id: int, req: DecisionRequest, x_api_key: Optional[str] = Header(default=None)):
    require_key(x_api_key)
    with db() as c:
        row = c.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone()
        if not row: raise HTTPException(404, "Approval not found.")
        if row["status"] != "pending": raise HTTPException(409, "This item has already been decided.")
        status = "approved" if req.decision == "approve" else "rejected"
        c.execute("UPDATE approvals SET status=?,decided_at=? WHERE id=?", (status, now(), approval_id))
    return {"approval_id": approval_id, "status": status,
            "note": "Approval does not send email; delivery remains disabled until a mail provider is explicitly configured."}

@app.get("/tasks")
def list_tasks(x_api_key: Optional[str] = Header(default=None)):
    require_key(x_api_key)
    with db() as c:
        rows = c.execute("SELECT id,kind,status,input_json,output_json,error,created_at,updated_at FROM tasks ORDER BY id DESC LIMIT 100").fetchall()
    return {"items":[dict(r) for r in rows]}
