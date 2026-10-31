"""Read-only PeoplePerHour public project listing reader.

Requests only the public listing URL with the page parameter. It extracts
embedded listing state without a browser, stores no client names, and never
bids, applies, or messages.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import hashlib
import json
import re

USER_AGENT = "TradingLab03OpportunityScout/1.0 (+public-project-reader)"
MAX_BYTES = 2_000_000
STATE_MARKER = "window.PPHReact.initialState="


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
        return re.sub(r"<[^>]*>", " ", value or "").strip()


def _extract_state(html: str):
    index = html.find(STATE_MARKER)
    if index < 0:
        raise ValueError("PeoplePerHour listing state marker not found; page may have changed")
    tail = html[index + len(STATE_MARKER):]
    try:
        state, _ = json.JSONDecoder().raw_decode(tail)
    except ValueError as exc:
        raise ValueError("Could not decode PeoplePerHour listing state") from exc
    if not isinstance(state, dict):
        raise ValueError("PeoplePerHour listing state was not an object")
    return state


def fetch_projects(source: dict, score_listing, timeout: int = 12) -> list[dict]:
    base = str(source.get("url") or "https://www.peopleperhour.com/freelance-jobs").rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme != "https" or parsed.hostname not in {"www.peopleperhour.com", "peopleperhour.com"}:
        raise ValueError("PeoplePerHour source must use its official HTTPS listing host")
    request = Request(f"{base}?page=1", headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    })
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"PeoplePerHour returned HTTP {response.status}")
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("PeoplePerHour page exceeded 2 MB limit")
    html = body.decode("utf-8", errors="replace")
    state = _extract_state(html)
    entities = ((state.get("entities") or {}).get("projects") or {})
    if not isinstance(entities, dict):
        raise ValueError("PeoplePerHour listing state did not contain project records")

    out = []
    for entity in entities.values():
        if not isinstance(entity, dict):
            continue
        raw = entity.get("attributes") or {}
        if raw.get("item_type") and raw.get("item_type") != "job":
            continue
        project_id = str(raw.get("proj_id") or entity.get("id") or "").strip()
        title = clean_html(str(raw.get("title") or "")).strip()
        description = clean_html(str(raw.get("proj_desc") or ""))[:3000]
        url = str(raw.get("url") or "").strip()
        if url.startswith("/"):
            url = "https://www.peopleperhour.com" + url
        url_parts = urlparse(url)
        if not project_id or not title or url_parts.scheme != "https" or url_parts.hostname not in {
            "www.peopleperhour.com", "peopleperhour.com"
        }:
            continue
        metadata = " ".join(str(raw.get(k) or "") for k in ("project_type", "location_type"))
        scored = score_listing(title, description + " " + metadata, source.get("name", "PeoplePerHour"))
        ident = hashlib.sha256((url + title).encode("utf-8")).hexdigest()[:16]
        out.append({
            "id": ident,
            "title": title,
            "url": url,
            "description": description,
            "published": str(raw.get("posted_dt") or ""),
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            **scored,
            "status": "new_lead",
            "paid_contract_verified": False,
            "next_step": "Human verifies project is open, payment, eligibility, budget, and platform rules before bidding.",
        })
    return out
