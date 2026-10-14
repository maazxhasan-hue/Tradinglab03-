"""Read-only Freelancer.com project discovery, with a free public endpoint fallback."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

API_URL = "https://www.freelancer.com/api/projects/0.1/projects/active/"
USER_AGENT = "TradingLab03OpportunityScout/1.0 (+public-project-reader)"
MAX_BYTES = 2_000_000


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get(self):
        return " ".join(" ".join(self.parts).split())


def clean_html(value: str) -> str:
    parser = _Text()
    try:
        parser.feed(value or "")
        return parser.get()
    except Exception:
        return value or ""


def _projects_from_payload(payload):
    """Accept the common response wrappers used by the API and SDK."""
    for key in ("result", "data", "response"):
        if isinstance(payload, dict) and isinstance(payload.get(key), (dict, list)):
            payload = payload[key]
            break
    if isinstance(payload, dict):
        projects = next(
            (payload[k] for k in ("projects", "items", "results")
             if isinstance(payload.get(k), list)),
            None,
        )
        if projects is None:
            raise ValueError("Freelancer API response did not contain a project list")
        return projects
    if isinstance(payload, list):
        return payload
    raise ValueError("Freelancer API response did not contain a project list")


def _canonical_project_url(project: dict) -> str:
    raw = str(project.get("seo_url") or project.get("url") or project.get("project_url") or "").strip()
    if raw.startswith("https://"):
        return raw
    if raw.startswith("/"):
        return "https://www.freelancer.com" + raw
    # Public API records can contain a SEO slug rather than an absolute URL.
    slug = raw.strip("/")
    project_id = str(project.get("id") or project.get("project_id") or "").strip()
    if slug and project_id and not slug.isdigit():
        return f"https://www.freelancer.com/projects/{slug}/{project_id}"
    if project_id:
        return f"https://www.freelancer.com/projects/{project_id}"
    return ""


def _normalise_projects(projects, source: dict, score_listing) -> list[dict]:
    out = []
    for project in projects:
        if not isinstance(project, dict):
            continue
        title = str(project.get("title") or project.get("name") or "").strip()
        description = clean_html(str(
            project.get("description") or project.get("preview_description") or ""
        ))[:3000]
        url = _canonical_project_url(project)
        if not title or urlparse(url).scheme != "https" or urlparse(url).hostname not in {
            "www.freelancer.com", "freelancer.com"
        }:
            continue
        scored = score_listing(title, description, source.get("name", "Freelancer.com"))
        ident = hashlib.sha256((url + title).encode("utf-8")).hexdigest()[:16]
        out.append({
            "id": ident,
            "title": title,
            "url": url,
            "description": description,
            "published": str(project.get("time_submitted") or project.get("submitdate") or ""),
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            **scored,
            "status": "new_lead",
            "paid_contract_verified": False,
            "next_step": "Human verifies project is open, eligible, legitimate, and paid before any proposal.",
        })
    return out


def fetch_public_projects(source: dict, score_listing, timeout: int = 12) -> list[dict]:
    """Read publicly listed active projects without a paid service or API token.

    This is read-only and intentionally performs one bounded GET per scout run.
    It never bids, messages, applies, or interacts with accounts.
    """
    limit = min(max(int(source.get("limit", 50)), 1), 50)
    params = {"limit": limit}
    query = str(source.get("query") or "").strip()
    if query:
        params["query"] = query
    request = Request(
        API_URL + "?" + urlencode(params),
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Freelancer public API returned HTTP {response.status}")
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("Freelancer public API response exceeded 2 MB limit")
    return _normalise_projects(_projects_from_payload(json.loads(body.decode("utf-8"))), source, score_listing)


def fetch_projects(source: dict, token: str, score_listing) -> list[dict]:
    """Use the official SDK when an authorized token is configured."""
    from freelancersdk.session import Session
    from freelancersdk.resources.projects.projects import search_projects

    session = Session(oauth_token=token)
    limit = min(max(int(source.get("limit", 50)), 1), 100)
    query = str(source.get("query") or "website wordpress ecommerce web design video editing SEO automation")
    response = search_projects(session, query=query, limit=limit, offset=0, active_only=True)
    return _normalise_projects(_projects_from_payload(response), source, score_listing)
