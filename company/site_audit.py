"""Fetch and audit a public business homepage for visible service opportunities.

Only a single HTTPS page is fetched. Private/local destinations are rejected.
This does not collect personal data, submit forms, crawl the site, or contact anyone.
"""
from __future__ import annotations
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import ipaddress, socket

MAX_BYTES = 1_000_000
TIMEOUT_SECONDS = 8
USER_AGENT = "TradingLab03SiteAudit/1.0 (+single-page business audit)"

class AuditParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title_parts = []
        self.in_title = False
        self.description = ""
        self.viewport = False
        self.h1_count = 0
        self.forms = 0
        self.images = 0
        self.images_without_alt = 0
        self.links = []
        self.text_parts = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title": self.in_title = True
        if tag == "meta" and attrs.get("name", "").casefold() == "description":
            self.description = attrs.get("content", "").strip()
        if tag == "meta" and attrs.get("name", "").casefold() == "viewport":
            self.viewport = True
        if tag == "h1": self.h1_count += 1
        if tag == "form": self.forms += 1
        if tag == "img":
            self.images += 1
            if not attrs.get("alt", "").strip(): self.images_without_alt += 1
        if tag == "a" and attrs.get("href"):
            self.links.append((attrs.get("href", ""), attrs.get("aria-label", "")))
    def handle_endtag(self, tag):
        if tag == "title": self.in_title = False
    def handle_data(self, data):
        if self.in_title: self.title_parts.append(data)
        if data.strip(): self.text_parts.append(data.strip())

def validate_public_https_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Only public HTTPS URLs without embedded credentials are allowed")
    host = parsed.hostname
    if host.casefold() in {"localhost", "localhost.localdomain"}:
        raise ValueError("Local hosts are not allowed")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)}
    except OSError as exc:
        raise ValueError("Could not resolve public website host") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValueError("Private, local, or reserved network destinations are not allowed")
    return url

def analyze_html(url: str, html_text: str) -> dict:
    parser = AuditParser()
    parser.feed(html_text[:MAX_BYTES])
    title = " ".join(" ".join(parser.title_parts).split())
    text = " ".join(parser.text_parts).casefold()
    links_text = " ".join((href + " " + label).casefold() for href, label in parser.links)
    findings = []
    if not title: findings.append({"need":"missing page title", "service":"SEO metadata setup", "evidence":"Homepage contains no detectable title element"})
    if not parser.description: findings.append({"need":"missing meta description", "service":"SEO metadata setup", "evidence":"Homepage contains no detectable meta description"})
    if not parser.viewport: findings.append({"need":"missing mobile viewport", "service":"responsive website audit", "evidence":"Homepage contains no viewport meta tag"})
    if parser.h1_count == 0: findings.append({"need":"missing primary heading", "service":"website copy and accessibility review", "evidence":"No H1 heading detected"})
    if parser.images and parser.images_without_alt: findings.append({"need":"images missing alternative text", "service":"accessibility improvement", "evidence":f"{parser.images_without_alt} of {parser.images} image tags lack alt text"})
    if not parser.forms and not any(x in links_text for x in ("contact", "book", "appointment", "quote", "enquiry", "inquiry")):
        findings.append({"need":"no obvious contact or booking path", "service":"lead capture or booking workflow", "evidence":"No form or recognizable contact/booking link detected"})
    if not any(x in links_text or x in text for x in ("shop", "cart", "checkout", "product")):
        findings.append({"need":"no obvious e-commerce path", "service":"optional e-commerce review", "evidence":"No recognizable store/cart/product signals detected; verify manually"})
    return {
        "url": url, "page_title": title, "meta_description_present": bool(parser.description),
        "mobile_viewport_present": parser.viewport, "h1_count": parser.h1_count,
        "forms_detected": parser.forms, "images_detected": parser.images,
        "images_without_alt": parser.images_without_alt,
        "findings": findings,
        "limitations": ["Single-page heuristic audit only", "Absence of a signal is not proof the business needs a service",
                       "Human must verify findings before outreach or proposal"],
    }

def audit_public_homepage(url: str) -> dict:
    safe_url = validate_public_https_url(url)
    request = Request(safe_url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        if response.status != 200:
            raise RuntimeError(f"Homepage returned HTTP {response.status}")
        content_type = response.headers.get("Content-Type", "").casefold()
        if "text/html" not in content_type:
            raise ValueError("URL did not return an HTML page")
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        body = body[:MAX_BYTES]
    html_text = body.decode("utf-8", errors="replace")
    return analyze_html(safe_url, html_text)
