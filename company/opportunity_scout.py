"""Hourly public opportunity scout. Reads allowlisted RSS/Atom feeds; never contacts prospects.

Configure feeds in config/opportunity_sources.json. The scout ranks public listings
as leads, not guaranteed paid contracts, and writes a local JSON/Markdown report.
"""
from __future__ import annotations
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import json
import re
import hashlib
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "config" / "opportunity_sources.json"
OUT_DIR = ROOT / "data" / "opportunities"
USER_AGENT = "TradingLab03OpportunityScout/1.0 (+public-feed-reader)"
MAX_BYTES = 2_000_000
ALLOWED_SCHEMES = {"https"}

SERVICE_TERMS = {
    "website": 4, "web design": 5, "landing page": 4, "wordpress": 4,
    "shopify": 4, "ecommerce": 5, "e-commerce": 5, "redesign": 4,
    "frontend": 3, "full stack": 3, "seo": 3, "automation": 3,
    "video editing": 3, "short-form video": 3, "content": 2, "small business": 2,
    "freelance": 2, "contract": 2, "budget": 1, "paid": 2,
}
NEGATIVE_TERMS = {"unpaid test", "exposure only", "commission only", "crypto deposit", "pay to apply"}
CONTRACT_SIGNALS = (
    "freelance", "freelancer", "independent contractor", "contractor", "contract-based",
    "contract role", "contract position", "fixed-price", "fixed price", "project-based",
    "project based", "paid project", "client project", "freelance project",
)
# Signals that indicate a purchasable project/service request rather than a job vacancy.
# Explicit buyer-intent wording: a business is seeking a deliverable, not merely filling a role.
PROJECT_SIGNALS = (
    "looking for a freelancer to", "hire a freelancer to", "seeking a freelancer to",
    "need a website", "need a landing page", "need someone to build",
    "need someone to design", "looking for someone to build", "looking for someone to design",
    "seeking a developer to build", "seeking a designer to create",
    "request for proposal", "rfp for website", "requesting proposals for",
    "looking for an agency to", "seeking an agency to",
    "our business needs a website", "business needs a landing page",
    "we need a website", "we need a landing page", "we need help redesigning",
    "project brief: build", "project brief: design",
    "looking for a web designer", "looking for a website designer",
    "need a web designer", "need a website designer", "need a developer for our website",
    "looking for an seo specialist for our business", "need seo help for my business",
    "looking for a video editor for my channel", "need a video editor for my business",
    "looking for someone to edit our videos", "seeking a wordpress developer for our site",
    "need help with our shopify store", "looking for help with our shopify store",
    "budget is", "budget:", "paid gig", "paid freelance project",
)
# Role-filling wording is disqualifying for client buyer intent, but a listing can
# still qualify as a separate freelance-work opportunity.
JOB_VACANCY_SIGNALS = (
    "we are hiring", "we're hiring", "join our team", "join our team as",
    "apply for this role", "job opening", "full-time position", "full time position",
    "salary and benefits", "benefits package", "your responsibilities will",
    "submit your resume", "submit a resume", "employment type", "about the role",
    "we are looking to fill", "we're looking to fill",
)
FREELANCE_WORK_SIGNALS = (
    "freelance", "freelancer", "independent contractor", "project-based",
    "project based", "paid projects", "rate of pay", "per completed task",
    "per article", "per word", "paid per",
)
PERMANENT_ROLE_SIGNALS = (
    "full-time", "full time", "permanent employee", "employee position",
    "salary and benefits", "benefits package", "full-time ongoing position",
)
EMPLOYMENT_SIGNALS = (
    "full-time", "full time", "permanent employee", "employee position", "salary and benefits",
    "head of ", "director of ", "vice president", "vp of ", "chief ", "internship",
)
LOCATION_RESTRICTIONS = (
    "onsite", "on-site", "in-office", "in office", "u.s. based", "us-based", "usa only",
    "united states only", "must be based in the united states", "must be based in the us",
    "remote us only", "remote - us", "us residents only", "u.s. residents only",
)
TITLE_LOCATION_RESTRICTIONS = (
    " - united states", "- united states", "(united states)", " - us only", "(us only)",
    " - u.s. only", "(u.s. only)", " - usa only", "(usa only)",
)

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)
    def text(self):
        return " ".join(" ".join(self.parts).split())

def _clean_html(raw: str) -> str:
    parser = TextExtractor()
    try:
        parser.feed(raw or "")
        return parser.text()
    except Exception:
        return re.sub(r"<[^>]*>", " ", raw or "").strip()

def load_sources() -> list[dict]:
    if not SOURCES_PATH.exists():
        return []
    data = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Opportunity source config must be a JSON list")
    enabled = [item for item in data if item.get("enabled", True)]
    for item in enabled:
        url = item.get("url", "")
        parsed = urlparse(url)
        if parsed.scheme not in ALLOWED_SCHEMES or not parsed.hostname:
            raise ValueError(f"Source must be an HTTPS URL: {url!r}")
    return enabled

def score_listing(title: str, description: str, source_name: str = "") -> dict:
    title_text = title.casefold()
    text = (title + " " + description).casefold()
    reasons = []
    score = 0
    for term, points in SERVICE_TERMS.items():
        if term in text:
            score += points
            reasons.append(f"service match: {term}")
    risk_flags = [term for term in NEGATIVE_TERMS if term in text]
    contract_signals = [term for term in CONTRACT_SIGNALS if term in text]
    project_signals = [term for term in PROJECT_SIGNALS if term in text]
    job_vacancy_signals = [term for term in JOB_VACANCY_SIGNALS if term in text]
    employment_signals = [term for term in EMPLOYMENT_SIGNALS if term in text]
    location_restrictions = [term for term in LOCATION_RESTRICTIONS if term in text]
    if any(term in title_text for term in TITLE_LOCATION_RESTRICTIONS):
        location_restrictions.append("country-restricted title")
    freelance_work_signals = [term for term in FREELANCE_WORK_SIGNALS if term in text]
    permanent_role_signals = [term for term in PERMANENT_ROLE_SIGNALS if term in text]
    if risk_flags:
        score -= 8 * len(risk_flags)

    # Separate direct buyer projects from job/gig opportunities. A role-filling ad
    # cannot be labelled a client buyer lead simply because it mentions clients.
    disqualifiers = list(risk_flags)
    if location_restrictions:
        disqualifiers.extend(location_restrictions)
    if not project_signals:
        disqualifiers.append("no explicit service-project request")
    if job_vacancy_signals:
        disqualifiers.extend(job_vacancy_signals)
    client_fit = bool(project_signals) and not disqualifiers

    # Freelance roles may be paid work, but are not direct client leads. Generic
    # "contractor" wording alone is insufficient. Exclude risky/location-restricted
    # and clearly permanent/full-time employee roles.
    freelance_work_fit = (
        not client_fit
        and bool(freelance_work_signals)
        and not risk_flags
        and not location_restrictions
        and not permanent_role_signals
    )
    if client_fit:
        opportunity_type = "client_project"
        reasons.append("explicit buyer-intent service request")
    elif freelance_work_fit:
        opportunity_type = "freelance_work"
        reasons.append("freelance/project/rate signal; not a direct client buyer lead")
    elif job_vacancy_signals or employment_signals:
        opportunity_type = "employment_role"
        reasons.append("role/job-vacancy language detected")
    else:
        opportunity_type = "unqualified"
    if not project_signals:
        reasons.append("no explicit service-project request")
    if location_restrictions:
        reasons.append("location or on-site restriction detected")

    qualified = client_fit or freelance_work_fit
    priority = "high" if qualified and score >= 9 else ("review" if qualified and score >= 4 else "low")
    return {
        "score": max(0, min(100, score)),
        "reasons": reasons[:10],
        "risk_flags": risk_flags,
        "contract_signals": contract_signals,
        "project_signals": project_signals,
        "job_vacancy_signals": job_vacancy_signals,
        "employment_signals": employment_signals,
        "freelance_work_signals": freelance_work_signals,
        "permanent_role_signals": permanent_role_signals,
        "location_restrictions": location_restrictions,
        "disqualifiers": sorted(set(disqualifiers)),
        "client_fit": client_fit,
        "freelance_work_fit": freelance_work_fit,
        "opportunity_type": opportunity_type,
        "priority": priority,
        "source_name": source_name,
    }

def _first_text(node, names):
    for name in names:
        el = node.find(name)
        if el is not None and el.text:
            return el.text.strip()
    return ""

def parse_feed(xml_bytes: bytes, source: dict) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    items = root.findall(".//item")
    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = root.findall(".//atom:entry", ns)
    out = []
    for item in items:
        title = _first_text(item, ["title", "{http://www.w3.org/2005/Atom}title"])
        link = _first_text(item, ["link"])
        if not link:
            atom_link = item.find("{http://www.w3.org/2005/Atom}link")
            if atom_link is not None:
                link = atom_link.attrib.get("href", "")
        description = _first_text(item, ["description", "summary", "{http://www.w3.org/2005/Atom}summary", "content"])
        description = _clean_html(description)[:3000]
        published = _first_text(item, ["pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}updated"])
        if not title or not link:
            continue
        if urlparse(link).scheme != "https":
            continue
        scored = score_listing(title, description, source.get("name", "RSS feed"))
        ident = hashlib.sha256((link + title).encode("utf-8")).hexdigest()[:16]
        out.append({
            "id": ident, "title": _clean_html(title), "url": link, "description": description,
            "published": published, "discovered_at": datetime.now(timezone.utc).isoformat(),
            **scored, "status": "new_lead", "paid_contract_verified": False,
            "next_step": "Human verifies legitimacy, payment, scope, and platform rules before bidding.",
        })
    return out

def parse_remotive_api(body: bytes, source: dict) -> list[dict]:
    """Parse Remotive's documented JSON API as a fallback when its RSS feed fails."""
    payload = json.loads(body.decode("utf-8"))
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
    out = []
    for job in jobs:
        if not isinstance(job, dict):
            continue
        title = str(job.get("title") or "").strip()
        link = str(job.get("url") or "").strip()
        if not title or urlparse(link).scheme != "https":
            continue
        description = _clean_html(str(job.get("description") or ""))[:3000]
        metadata = " ".join(str(job.get(k) or "") for k in (
            "job_type", "candidate_required_location", "company_name"
        ))
        scored = score_listing(title, description + " " + metadata, source.get("name", "Remotive"))
        ident = hashlib.sha256((link + title).encode("utf-8")).hexdigest()[:16]
        out.append({
            "id": ident, "title": _clean_html(title), "url": link,
            "description": description, "published": str(job.get("publication_date") or ""),
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            **scored, "status": "new_lead", "paid_contract_verified": False,
            "next_step": "Human verifies legitimacy, payment, scope, location eligibility, and platform rules before bidding.",
        })
    return out


def fetch_feed(source: dict, timeout: int = 12) -> list[dict]:
    url = source["url"]
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise RuntimeError(f"Feed returned HTTP {response.status}")
            body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("Feed exceeded 2 MB limit")
        return parse_feed(body, source)
    except Exception:
        # Only the explicitly named Remotive source may use this fixed HTTPS fallback.
        if "remotive" not in str(source.get("name", "")).casefold():
            raise
        api_request = Request(
            "https://remotive.com/api/remote-jobs?limit=50",
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        with urlopen(api_request, timeout=timeout) as response:
            if response.status != 200:
                raise RuntimeError(f"Remotive API returned HTTP {response.status}")
            body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("Remotive API response exceeded 2 MB limit")
        return parse_remotive_api(body, source)

def discover(sources: list[dict] | None = None) -> dict:
    sources = load_sources() if sources is None else sources
    items, errors = {}, []
    for source in sources:
        try:
            for item in fetch_feed(source):
                previous = items.get(item["id"])
                if previous is None or item["score"] > previous["score"]:
                    items[item["id"]] = item
        except Exception as exc:
            errors.append({"source": source.get("name", source.get("url", "unknown")), "error": str(exc)[:300]})
    leads = sorted(
        items.values(),
        key=lambda x: (
            x.get("client_fit") is True,
            x.get("priority") == "high",
            x.get("freelance_work_fit") is True,
            x.get("score", 0),
        ),
        reverse=True,
    )
    type_counts = {}
    for item in leads:
        kind = item.get("opportunity_type", "unqualified")
        type_counts[kind] = type_counts.get(kind, 0) + 1
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources_configured": len(sources), "items_found": len(leads),
        "summary": {
            "client_projects": type_counts.get("client_project", 0),
            "freelance_work": type_counts.get("freelance_work", 0),
            "employment_roles": type_counts.get("employment_role", 0),
            "unqualified": type_counts.get("unqualified", 0),
            "high_priority": sum(x.get("priority") == "high" for x in leads),
            "review_priority": sum(x.get("priority") == "review" for x in leads),
            "low_priority": sum(x.get("priority") == "low" for x in leads),
        },
        "note": "Listings are unverified. Client projects are buyer-intent requests; freelance work listings are not direct client leads. Payment and eligibility are unverified. No messages, bids, or applications are sent.",
        "errors": errors, "opportunities": leads,
    }

def save_report(report: dict, output_dir: str | Path = OUT_DIR) -> tuple[Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = out / f"opportunities-{stamp}.json"
    md_path = out / f"opportunities-{stamp}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# TradingLab03 Opportunity Scout", "", f"Generated: {report['generated_at']}", "",
             f"- Sources configured: {report['sources_configured']}",
             f"- Listings found: {report['items_found']}", ""]
    summary = report.get("summary", {})
    if summary:
        lines.extend([
            "## Qualification summary", "",
            f"- Direct client-project requests: {summary.get('client_projects', 0)}",
            f"- Freelance work listings (not direct client leads): {summary.get('freelance_work', 0)}",
            f"- Employment-role listings: {summary.get('employment_roles', 0)}",
            f"- Unqualified / ambiguous: {summary.get('unqualified', 0)}",
            f"- High / review / low priority: {summary.get('high_priority', 0)} / {summary.get('review_priority', 0)} / {summary.get('low_priority', 0)}", ""
        ])
    lines.extend(["> Listings are unverified. No applications or messages were sent.", ""])
    for item in report["opportunities"]:
        lines.extend([f"## [{item['title']}]({item['url']})",
                      f"- Classification: {item.get('opportunity_type', 'unqualified')}",
                      f"- Priority: {item['priority']} (service score {item['score']})",
                      f"- Direct client-project request: {'yes' if item.get('client_fit') else 'no'}",
                      f"- Potential freelance work: {'yes' if item.get('freelance_work_fit') else 'no'}",
                      f"- Contract signals: {', '.join(item.get('contract_signals', [])) or 'none detected'}",
                      f"- Buyer/project signals: {', '.join(item.get('project_signals', [])) or 'none detected'}",
                      f"- Job-role signals: {', '.join(item.get('job_vacancy_signals', [])) or 'none detected'}",
                      f"- Disqualifiers: {', '.join(item.get('disqualifiers', [])) or 'none detected'}",
                      f"- Source: {item['source_name']}",
                      f"- Payment verified: no",
                      f"- Description: {item['description'][:500]}", ""])
    if report["errors"]:
        lines.extend(["## Source errors", ""])
        lines.extend(f"- {e['source']}: {e['error']}" for e in report["errors"])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path

def main():
    report = discover()
    json_path, md_path = save_report(report)
    print(json.dumps({
        "sources": report["sources_configured"],
        "found": report["items_found"],
        "summary": report.get("summary", {}),
        "source_errors": report["errors"],
        "json_report": str(json_path),
        "markdown_report": str(md_path),
        "error_count": len(report["errors"]),
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
