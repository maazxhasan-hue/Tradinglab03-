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
    for item in data:
        url = item.get("url", "")
        parsed = urlparse(url)
        if parsed.scheme not in ALLOWED_SCHEMES or not parsed.hostname:
            raise ValueError(f"Source must be an HTTPS URL: {url!r}")
    return data

def score_listing(title: str, description: str, source_name: str = "") -> dict:
    text = (title + " " + description).casefold()
    reasons = []
    score = 0
    for term, points in SERVICE_TERMS.items():
        if term in text:
            score += points
            reasons.append(f"service match: {term}")
    risk_flags = [term for term in NEGATIVE_TERMS if term in text]
    if risk_flags:
        score -= 8 * len(risk_flags)
    return {
        "score": max(0, min(100, score)),
        "reasons": reasons[:8],
        "risk_flags": risk_flags,
        "priority": "high" if score >= 9 and not risk_flags else ("review" if score >= 4 else "low"),
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

def fetch_feed(source: dict, timeout: int = 12) -> list[dict]:
    url = source["url"]
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Feed returned HTTP {response.status}")
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("Feed exceeded 2 MB limit")
    return parse_feed(body, source)

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
    leads = sorted(items.values(), key=lambda x: (x["priority"] == "high", x["score"]), reverse=True)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources_configured": len(sources), "items_found": len(leads),
        "note": "Listings are unverified leads, not guaranteed paid contracts. No messages, bids, or applications are sent.",
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
             f"- Listings found: {report['items_found']}", "",
             "> Leads are unverified. No applications or messages were sent.", ""]
    for item in report["opportunities"]:
        lines.extend([f"## [{item['title']}]({item['url']})",
                      f"- Priority: {item['priority']} (score {item['score']})",
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
    print(json.dumps({"sources": report["sources_configured"], "found": report["items_found"],
                      "json_report": str(json_path), "markdown_report": str(md_path),
                      "errors": len(report["errors"])}, ensure_ascii=False))

if __name__ == "__main__":
    main()
