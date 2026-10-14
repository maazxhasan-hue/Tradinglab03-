"""Read-only Freelancer.com API adapter for TradingLab03 opportunity discovery."""
from __future__ import annotations
import hashlib
from datetime import datetime, timezone
from html.parser import HTMLParser

class _Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_data(self, data): self.parts.append(data)
    def get(self): return " ".join(" ".join(self.parts).split())

def clean_html(value: str) -> str:
    parser = _Text()
    try:
        parser.feed(value or "")
        return parser.get()
    except Exception:
        return value or ""

def fetch_projects(source: dict, token: str, score_listing) -> list[dict]:
    """Fetch active projects using the official SDK; no bidding or messaging."""
    from freelancersdk.session import Session
    from freelancersdk.resources.projects.projects import search_projects
    session = Session(oauth_token=token)
    limit = min(max(int(source.get("limit", 50)), 1), 100)
    query = str(source.get("query") or "website wordpress ecommerce web design video editing SEO automation")
    response = search_projects(session, query=query, limit=limit, offset=0, active_only=True)
    payload = response
    if isinstance(payload, dict):
        for key in ("result", "data", "response"):
            if isinstance(payload.get(key), (dict, list)):
                payload = payload[key]; break
    if isinstance(payload, dict):
        projects = next((payload[k] for k in ("projects", "items", "results") if isinstance(payload.get(k), list)), None)
    elif isinstance(payload, list):
        projects = payload
    else:
        projects = None
    if projects is None:
        raise ValueError("Freelancer API response did not contain a project list")
    out = []
    for project in projects:
        if not isinstance(project, dict): continue
        title = str(project.get("title") or project.get("name") or "").strip()
        description = clean_html(str(project.get("description") or project.get("preview_description") or ""))[:3000]
        project_id = str(project.get("id") or project.get("project_id") or "").strip()
        url = str(project.get("seo_url") or project.get("url") or project.get("project_url") or "").strip()
        if url and not url.startswith("https://"): url = ""
        if not title or not url: continue
        scored = score_listing(title, description, source.get("name", "Freelancer.com API"))
        ident = hashlib.sha256((url + title).encode("utf-8")).hexdigest()[:16]
        out.append({"id": ident, "title": title, "url": url, "description": description,
                    "published": str(project.get("time_submitted") or project.get("submitdate") or ""),
                    "discovered_at": datetime.now(timezone.utc).isoformat(), **scored,
                    "status": "new_lead", "paid_contract_verified": False,
                    "next_step": "Human verifies project is open, eligible, legitimate, and paid before any proposal."})
    return out
