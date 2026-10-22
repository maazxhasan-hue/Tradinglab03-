#!/usr/bin/env python3
"""Generate the public Render sitemap from indexable HTML pages in public-site/."""
from __future__ import annotations

from datetime import date
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public-site"
BASE = "https://nexora-ai-public.onrender.com"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
EXCLUDED_NAMES = {"404.html", "admin.html", "login.html", "thank-you.html", "thankyou.html"}
EXCLUDED_PARTS = {"admin", "tests", "test", "thank-you", "thankyou", "thank_you", "fixtures"}


class Metadata(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_depth = 0
        self.title = ""
        self.description = ""
        self.robots = ""
        self.canonical = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == "title":
            self.title_depth += 1
        if tag.lower() == "meta":
            name = (attrs.get("name") or "").lower()
            if name == "description":
                self.description = attrs.get("content", "").strip()
            elif name == "robots":
                self.robots = attrs.get("content", "").lower()
        if tag.lower() == "link" and (attrs.get("rel") or "").lower() == "canonical":
            self.canonical = (attrs.get("href") or "").strip()

    def handle_endtag(self, tag):
        if tag.lower() == "title" and self.title_depth:
            self.title_depth -= 1

    def handle_data(self, data):
        if self.title_depth:
            self.title += data


def last_modified(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    try:
        value = subprocess.check_output(
            ["git", "log", "-1", "--format=%cs", "--", relative],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL,
        ).strip()
        if value:
            return value
    except (OSError, subprocess.CalledProcessError):
        pass
    return date.today().isoformat()


def public_url(path: Path) -> str:
    relative = path.relative_to(PUBLIC).as_posix()
    if relative == "index.html":
        return BASE + "/"
    if relative.endswith("/index.html"):
        return BASE + "/" + relative[:-len("index.html")]
    return BASE + "/" + relative


def is_excluded(path: Path, meta: Metadata) -> bool:
    rel = path.relative_to(PUBLIC)
    if path.name.lower() in EXCLUDED_NAMES or rel.name.lower().startswith("test-"):
        return True
    if any(part.lower() in EXCLUDED_PARTS for part in rel.parts):
        return True
    if "noindex" in meta.robots or "nofollow" in meta.robots:
        return True
    return False


def main() -> None:
    urls: list[tuple[str, str]] = []
    errors: list[str] = []
    for path in sorted(PUBLIC.rglob("*.html")):
        if path.name == "404.html":
            continue
        parser = Metadata()
        parser.feed(path.read_text(encoding="utf-8"))
        if not parser.title.strip():
            errors.append(f"Missing title: {path.relative_to(ROOT)}")
        if not parser.description.strip():
            errors.append(f"Missing meta description: {path.relative_to(ROOT)}")
        if is_excluded(path, parser):
            continue
        url = public_url(path)
        if parser.canonical and parser.canonical.rstrip("/") != url.rstrip("/"):
            # Do not sitemap duplicate URLs whose canonical points elsewhere.
            continue
        urls.append((url, last_modified(path)))
    if errors:
        raise SystemExit("\n".join(errors))

    ET.register_namespace("", NS)
    root = ET.Element(f"{{{NS}}}urlset")
    for url, modified in urls:
        item = ET.SubElement(root, f"{{{NS}}}url")
        ET.SubElement(item, f"{{{NS}}}loc").text = url
        ET.SubElement(item, f"{{{NS}}}lastmod").text = modified
    sitemap = PUBLIC / "sitemap.xml"
    ET.indent(root, space="  ")
    sitemap.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8") + b"\n")
    print(f"Generated {sitemap.relative_to(ROOT)} with {len(urls)} indexable public URLs.")


if __name__ == "__main__":
    main()
