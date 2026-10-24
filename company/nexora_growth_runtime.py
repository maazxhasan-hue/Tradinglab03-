"""Durable, approval-gated Nexora 41-agent social growth workflow.

This module is a safe local/runtime foundation, not an external social connector.
SQLite persistence is real; agent roles are orchestration assignments. External
publishing and contact are intentionally unavailable until a verified connector
is implemented and server-side approval is recorded.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT.parent / "data" / "nexora_growth.sqlite3"
CONTENT_ACTIONS = {"publish_content", "send_public_reply", "send_direct_message", "send_email", "place_phone_call"}
SENSITIVE_ACTIONS = CONTENT_ACTIONS | {"paid_promotion", "make_purchase", "change_price", "change_permissions"}
STATES = {"queued", "running", "needs_review", "blocked", "failed", "completed"}
DEPARTMENTS = [
    ("Content Engine", ["Content Lead", "Content Strategist", "Script & Copywriter", "Video/Creative Producer", "Content QA & Repurposing Specialist"]),
    ("Market & Audience Intelligence", ["Research Lead", "Market Trend Analyst", "Audience/ICP Researcher", "Competitor Intelligence Analyst", "Keyword & Topic Researcher"]),
    ("Lead Intelligence", ["Lead Intelligence Lead", "Inbound Intent Classifier", "Public Prospect Researcher", "Lead Enrichment & Source Tracker", "Lead Quality Reviewer"]),
    ("Sales & Conversion", ["Sales Conversion Lead", "Enquiry Qualifier", "Proposal & Scope Drafter", "Follow-up Planner", "Meeting & Calendar Coordinator"]),
    ("Community & Customer Experience", ["Community Lead", "Comment & DM Triage Agent", "Customer Support Drafter", "Feedback & Review Analyst", "Response Escalation Specialist"]),
    ("Distribution & Search", ["Distribution Lead", "Social Scheduling Coordinator", "SEO & Website Distribution Specialist", "Campaign Link & UTM Manager", "Campaign QA Specialist"]),
    ("Analytics & Growth Experiments", ["Growth Analytics Lead", "Content Performance Analyst", "Funnel & Attribution Analyst", "Experiment Planner", "Reporting Specialist"]),
    ("Quality, Risk & Operations", ["Quality & Operations Lead", "Brand/Claims Reviewer", "Privacy, Consent & Platform Policy Reviewer", "Workflow Reliability & Audit Agent", "Compliance Audit Specialist"]),
]
AGENTS = [{"agent_id": "growth-director", "name": "Growth Director", "department": "Executive", "kind": "director"}]
for index, (department, roles) in enumerate(DEPARTMENTS, 1):
    for role_index, name in enumerate(roles):
        AGENTS.append({"agent_id": f"d{index:02d}-a{role_index+1:02d}", "name": name,
                       "department": department, "kind": "lead" if role_index == 0 else "specialist"})
assert len(AGENTS) == 41
assert sum(a["kind"] == "lead" for a in AGENTS) == 8
assert sum(a["kind"] == "specialist" for a in AGENTS) == 32

def _load_company_agents() -> list[dict[str, str]]:
    """Load the wider company role registry without changing the canonical 41 growth roles."""
    registry_path = ROOT / "roles.json"
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Company role registry is missing or invalid.") from exc
    if not isinstance(registry, list):
        raise RuntimeError("Company role registry must be a list.")
    company_agents: list[dict[str, str]] = []
    seen: set[str] = set()
    for department in registry:
        if not isinstance(department, dict):
            continue
        department_name = str(department.get("department", "Company Operations")).strip()[:120]
        roles = department.get("roles", [])
        if not isinstance(roles, list):
            continue
        for role in roles:
            if not isinstance(role, str) or not role.strip():
                continue
            name = role.strip()[:100]
            if name.casefold() in seen:
                continue
            seen.add(name.casefold())
            slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-")
            while "--" in slug:
                slug = slug.replace("--", "-")
            company_agents.append({
                "agent_id": "company-" + slug[:80],
                "name": name,
                "department": department_name,
                "kind": "company-specialist",
            })
    if not company_agents:
        raise RuntimeError("Company role registry contains no usable roles.")
    return company_agents


COMPANY_AGENTS = _load_company_agents()
AGENT_DIRECTORY = {agent["agent_id"]: agent for agent in [*AGENTS, *COMPANY_AGENTS]}

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

class GrowthStore:
    def __init__(self, db_path: str | Path = DEFAULT_DB):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def connect(self):
        con = sqlite3.connect(self.db_path, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        return con

    def _init(self):
        with self.connect() as con:
            con.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS tasks (
              task_id TEXT PRIMARY KEY, title TEXT NOT NULL, agent_id TEXT NOT NULL,
              department TEXT NOT NULL, status TEXT NOT NULL, inputs_json TEXT NOT NULL,
              outputs_json TEXT NOT NULL DEFAULT '{}', evidence_json TEXT NOT NULL DEFAULT '[]',
              next_tasks_json TEXT NOT NULL DEFAULT '[]', campaign_id TEXT,
              approval_id TEXT, error TEXT, retry_count INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
              FOREIGN KEY(approval_id) REFERENCES approvals(approval_id)
            );
            CREATE TABLE IF NOT EXISTS approvals (
              approval_id TEXT PRIMARY KEY, action TEXT NOT NULL, resource_id TEXT NOT NULL,
              requester TEXT NOT NULL, approver TEXT, approved INTEGER NOT NULL DEFAULT 0,
              decision TEXT NOT NULL DEFAULT 'pending', reason TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL, decided_at TEXT
            );
            CREATE TABLE IF NOT EXISTS audit (
              event_id TEXT PRIMARY KEY, actor TEXT NOT NULL, event_type TEXT NOT NULL,
              resource_id TEXT NOT NULL, details_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS brain_memories (
              memory_key TEXT PRIMARY KEY, summary TEXT NOT NULL, content_json TEXT NOT NULL,
              tags_json TEXT NOT NULL DEFAULT '[]', source_agent TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_brain_memories_created ON brain_memories(created_at);
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status, created_at);
            CREATE INDEX IF NOT EXISTS idx_approval_decision ON approvals(decision, created_at);
            """)

    def _audit(self, con, actor, event_type, resource_id, details):
        con.execute("INSERT INTO audit VALUES (?,?,?,?,?,?)",
                    (str(uuid.uuid4()), actor, event_type, resource_id,
                     json.dumps(details, sort_keys=True), now()))

    def create_task(self, title: str, agent_id: str, inputs: dict[str, Any] | None = None,
                    campaign_id: str | None = None) -> dict:
        agent = AGENT_DIRECTORY.get(agent_id)
        if not agent:
            raise ValueError("Unknown agent_id")
        if not title.strip():
            raise ValueError("Task title is required")
        task_id, timestamp = str(uuid.uuid4()), now()
        with self.connect() as con:
            con.execute("""INSERT INTO tasks(task_id,title,agent_id,department,status,inputs_json,
                        campaign_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)""",
                        (task_id,title.strip(),agent_id,agent["department"],"queued",
                         json.dumps(inputs or {},sort_keys=True),campaign_id,timestamp,timestamp))
            self._audit(con, agent_id, "task_created", task_id, {"title":title.strip()})
        return self.get_task(task_id)

    def get_task(self, task_id: str) -> dict:
        with self.connect() as con:
            row = con.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if not row:
            raise KeyError("Task not found")
        item = dict(row)
        for key, column in [("inputs","inputs_json"),("outputs","outputs_json"),
                            ("evidence_refs","evidence_json"),("next_task_ids","next_tasks_json")]:
            item[key] = json.loads(item.pop(column))
        return item

    def list_tasks(self, status: str | None = None, limit: int = 100) -> list[dict]:
        if status and status not in STATES:
            raise ValueError("Invalid task status")
        limit = max(1, min(int(limit), 250))
        with self.connect() as con:
            rows = con.execute("SELECT task_id FROM tasks" + (" WHERE status=?" if status else "")
                               + " ORDER BY created_at DESC LIMIT ?", ((status, limit) if status else (limit,))).fetchall()
        return [self.get_task(row["task_id"]) for row in rows]

    def transition(self, task_id: str, status: str, actor: str, outputs: dict | None = None,
                   evidence_refs: list | None = None, error: str | None = None) -> dict:
        if status not in STATES:
            raise ValueError("Invalid task status")
        with self.connect() as con:
            row = con.execute("SELECT status FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if not row:
                raise KeyError("Task not found")
            current = row["status"]
            allowed = {"queued":{"running","blocked"}, "running":{"needs_review","blocked","failed","completed"},
                       "needs_review":{"queued","blocked"}, "blocked":{"queued"}, "failed":{"queued"},"completed":set()}
            if status not in allowed[current]:
                raise ValueError(f"Invalid transition: {current} -> {status}")
            if status == "completed" and not (outputs is not None and evidence_refs):
                raise ValueError("Completion requires outputs and evidence references")
            con.execute("""UPDATE tasks SET status=?,outputs_json=COALESCE(?,outputs_json),
                        evidence_json=COALESCE(?,evidence_json),error=?,updated_at=? WHERE task_id=?""",
                        (status,json.dumps(outputs,sort_keys=True) if outputs is not None else None,
                         json.dumps(evidence_refs) if evidence_refs is not None else None,error,now(),task_id))
            self._audit(con, actor, "task_transition", task_id, {"from":current,"to":status,"error":error})
        return self.get_task(task_id)

    def requeue_interrupted_tasks(self, limit: int = 250) -> int:
        """Recover tasks left running by a process restart; preserve their audit trail."""
        limit = max(1, min(int(limit), 250))
        timestamp = now()
        with self.connect() as con:
            rows = con.execute(
                "SELECT task_id FROM tasks WHERE status='running' ORDER BY updated_at LIMIT ?", (limit,)
            ).fetchall()
            ids = [row["task_id"] for row in rows]
            for task_id in ids:
                con.execute(
                    "UPDATE tasks SET status='queued', error=?, updated_at=? WHERE task_id=? AND status='running'",
                    ("Recovered after worker process restart; safe to retry.", timestamp, task_id),
                )
                self._audit(con, "worker-recovery", "task_requeued_after_restart", task_id,
                            {"reason": "interrupted_running_task"})
        return len(ids)

    def remember_memory(self, memory_key: str, summary: str, content: dict,
                        tags: list[str] | None = None, source_agent: str = "company-brain") -> dict:
        if not memory_key.strip() or len(memory_key) > 160:
            raise ValueError("memory_key must be 1-160 characters")
        summary = summary.strip()[:2000]
        encoded = json.dumps(content, ensure_ascii=False, sort_keys=True)
        if len(encoded) > 20000:
            raise ValueError("Brain memory content exceeds 20 KB")
        with self.connect() as con:
            con.execute(
                """INSERT INTO brain_memories(memory_key,summary,content_json,tags_json,source_agent,created_at)
                   VALUES(?,?,?,?,?,?)
                   ON CONFLICT(memory_key) DO UPDATE SET summary=excluded.summary,
                     content_json=excluded.content_json,tags_json=excluded.tags_json,
                     source_agent=excluded.source_agent,created_at=excluded.created_at""",
                (memory_key, summary, encoded, json.dumps((tags or [])[:20]), source_agent[:100], now()),
            )
            self._audit(con, source_agent[:100], "brain_memory_saved", memory_key, {"summary": summary[:200]})
        return {"memory_key": memory_key, "summary": summary, "source_agent": source_agent[:100]}

    def recall_memories(self, query: str, limit: int = 5) -> list[dict]:
        limit = max(1, min(int(limit), 10))
        tokens = [token.casefold() for token in query.split() if len(token) >= 4][:12]
        with self.connect() as con:
            rows = con.execute(
                "SELECT memory_key,summary,content_json,tags_json,source_agent,created_at FROM brain_memories ORDER BY created_at DESC LIMIT 250"
            ).fetchall()
        ranked = []
        for row in rows:
            haystack = (str(row["summary"]) + " " + str(row["content_json"])).casefold()
            score = sum(1 for token in tokens if token in haystack)
            if not tokens or score:
                ranked.append((score, row))
        ranked.sort(key=lambda pair: (pair[0], pair[1]["created_at"]), reverse=True)
        results = []
        for _, row in ranked[:limit]:
            try:
                content = json.loads(row["content_json"])
                tags = json.loads(row["tags_json"])
            except (TypeError, json.JSONDecodeError):
                content, tags = {}, []
            results.append({"memory_key": row["memory_key"], "summary": row["summary"],
                            "content": content, "tags": tags, "source_agent": row["source_agent"],
                            "created_at": row["created_at"]})
        return results

    def memory_count(self) -> int:
        with self.connect() as con:
            row = con.execute("SELECT COUNT(*) AS n FROM brain_memories").fetchone()
        return int(row["n"])

    def request_approval(self, action: str, resource_id: str, requester: str) -> dict:
        if action not in SENSITIVE_ACTIONS:
            raise ValueError("Approval requests are reserved for registered sensitive actions")
        if not all(x.strip() for x in (resource_id, requester)):
            raise ValueError("Resource and requester are required")
        approval_id, timestamp = str(uuid.uuid4()), now()
        with self.connect() as con:
            con.execute("INSERT INTO approvals VALUES(?,?,?,?,NULL,0,'pending','',?,NULL)",
                        (approval_id,action,resource_id,requester,timestamp))
            self._audit(con, requester, "approval_requested", approval_id, {"action":action,"resource_id":resource_id})
        return {"approval_id":approval_id,"action":action,"resource_id":resource_id,"decision":"pending"}

    def decide_approval(self, approval_id: str, approver: str, approved: bool, reason: str) -> dict:
        if not approver.strip() or not reason.strip():
            raise ValueError("Approver and decision reason are required")
        with self.connect() as con:
            row = con.execute("SELECT * FROM approvals WHERE approval_id=?", (approval_id,)).fetchone()
            if not row:
                raise KeyError("Approval not found")
            if row["decision"] != "pending":
                raise ValueError("Approval has already been decided")
            if approver == row["requester"]:
                raise ValueError("Requester cannot approve their own action")
            decision = "approved" if approved else "rejected"
            con.execute("UPDATE approvals SET approver=?,approved=?,decision=?,reason=?,decided_at=? WHERE approval_id=?",
                        (approver,int(approved),decision,reason,now(),approval_id))
            self._audit(con, approver, "approval_decided", approval_id, {"decision":decision,"reason":reason})
            return {"approval_id":approval_id,"action":row["action"],"resource_id":row["resource_id"],
                    "requester":row["requester"],"approver":approver,"approved":bool(approved),
                    "decision":decision,"reason":reason}

    def authorize_external_action(self, approval_id: str, action: str, resource_id: str) -> tuple[bool,str]:
        """Fail closed; this only checks authorization and does not perform the external action."""
        with self.connect() as con:
            row = con.execute("SELECT * FROM approvals WHERE approval_id=?", (approval_id,)).fetchone()
            if not row:
                return False, "Approval record not found"
            if row["decision"] != "approved" or not row["approved"] or not row["approver"]:
                return False, "Explicit human approval is not recorded"
            if row["action"] != action or row["resource_id"] != resource_id:
                return False, "Approval does not match this action and resource"
            self._audit(con, "policy-check", "external_action_authorized", resource_id,
                        {"approval_id":approval_id,"action":action})
            return True, "Approval matched; external connector must still enforce this check before execution"

    def overview(self) -> dict:
        with self.connect() as con:
            counts = {row["status"]:row["n"] for row in con.execute("SELECT status,COUNT(*) n FROM tasks GROUP BY status")}
            pending = con.execute("SELECT COUNT(*) n FROM approvals WHERE decision='pending'").fetchone()["n"]
            total_approvals = con.execute("SELECT COUNT(*) n FROM approvals").fetchone()["n"]
            audit_events = con.execute("SELECT COUNT(*) n FROM audit").fetchone()["n"]
        department_count = len({agent["department"] for agent in AGENT_DIRECTORY.values()})
        return {"agent_roles_defined":len(AGENT_DIRECTORY),"growth_roles_defined":len(AGENTS),
                "company_roles_defined":len(COMPANY_AGENTS),"departments":department_count,"task_counts":counts,
                "pending_approvals":pending,"approval_records":total_approvals,"audit_events":audit_events,
                "brain":{"mode":"shared_local_sqlite_with_optional_supabase_sync","memory_records":self.memory_count()},
                "runtime_status":"SQLite_task_and_local_brain_store_available; restart durability depends on the deployment storage mount; live provider and remote brain readiness must be checked separately"}
