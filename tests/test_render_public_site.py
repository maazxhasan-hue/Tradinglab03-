"""Regression checks for the separately published Nexora Render site."""
from html.parser import HTMLParser
from pathlib import Path
import posixpath
import unittest
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public-site"
LIVE_HOST = "https://nexora-ai-public.onrender.com"


class AssetLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ("href", "src") and value:
                self.links.append(value.strip())


class RenderPublicSiteTests(unittest.TestCase):
    def test_published_html_local_links_and_assets_exist(self):
        html_files = sorted(PUBLIC.rglob("*.html"))
        self.assertTrue(html_files, "public-site must contain HTML pages")
        for file_path in html_files:
            parser = AssetLinks()
            parser.feed(file_path.read_text(encoding="utf-8"))
            for raw in parser.links:
                parts = urlsplit(raw)
                if parts.scheme or parts.netloc or not parts.path:
                    continue
                if parts.path.startswith("//"):
                    continue
                if parts.path.startswith("/"):
                    target = posixpath.normpath(parts.path.lstrip("/"))
                else:
                    target = posixpath.normpath(posixpath.join(
                        file_path.relative_to(PUBLIC).parent.as_posix(), parts.path
                    ))
                # normpath removes trailing slashes; preserve directory-link intent
                # from the original URL so /pricing/ resolves to pricing/index.html.
                if parts.path.endswith("/") and target not in ("", "."):
                    target = posixpath.join(target, "index.html")
                if target in ("", "."):
                    target = "index.html"
                target_path = PUBLIC / target
                self.assertTrue(
                    target_path.is_file(),
                    f"Broken local link or asset in {file_path.relative_to(PUBLIC)}: {raw} -> {target}",
                )

    def test_public_site_has_no_retired_host_references(self):
        self.assertTrue((PUBLIC / "index.html").is_file())
        for file_path in PUBLIC.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in (".html", ".js", ".xml", ".txt"):
                body = file_path.read_text(encoding="utf-8")
                self.assertNotIn("nexora-ai-public.netlify.app", body, str(file_path))
                self.assertNotIn("nexoraai.vercel.app", body, str(file_path))
                self.assertNotIn("nexora-ai-sooty-two.vercel.app", body, str(file_path))

    def test_every_html_page_has_a_unique_title_and_description(self):
        import re

        html_files = sorted(PUBLIC.rglob("*.html"))
        self.assertTrue(html_files)
        titles = []
        for file_path in html_files:
            source = file_path.read_text(encoding="utf-8")
            title_match = re.search(r"<title\b[^>]*>(.*?)</title>", source, re.I | re.S)
            description_match = re.search(
                r"""<meta\b(?=[^>]*\bname=["']description["'])[^>]*\bcontent=["']([^"']*)["']""",
                source, re.I,
            )
            self.assertIsNotNone(title_match, f"Missing title: {file_path.relative_to(PUBLIC)}")
            self.assertIsNotNone(description_match, f"Missing description: {file_path.relative_to(PUBLIC)}")
            title = re.sub(r"\s+", " ", title_match.group(1)).strip()
            description = description_match.group(1).strip()
            self.assertTrue(title.endswith("| Nexora AI"), f"Title must end with '| Nexora AI': {file_path.relative_to(PUBLIC)}")
            self.assertTrue(description, f"Empty description: {file_path.relative_to(PUBLIC)}")
            self.assertLessEqual(len(description), 220, f"Description is too long: {file_path.relative_to(PUBLIC)}")
            titles.append(title)
        self.assertEqual(len(titles), len(set(titles)), "Every HTML page must have a unique title")

    def test_custom_404_page_is_published_and_has_helpful_navigation(self):
        page = PUBLIC / "404.html"
        self.assertTrue(page.is_file(), "Render static publish root needs its own 404.html")
        html = page.read_text(encoding="utf-8")
        for marker in ('<title>Page Not Found | Nexora AI</title>', 'href="/"', 'href="/pricing/"', 'href="/about/"', 'href="/blog/seo-guide/"'):
            self.assertIn(marker, html)
        self.assertIn('name="robots" content="noindex,nofollow"', html)

    def test_sitemap_and_robots_point_to_render(self):
        sitemap = PUBLIC / "sitemap.xml"
        robots = PUBLIC / "robots.txt"
        self.assertTrue(sitemap.is_file())
        self.assertTrue(robots.is_file())
        root = ET.parse(sitemap).getroot()
        locations = [
            node.text or ""
            for node in root.iter()
            if node.tag.endswith("loc")
        ]
        self.assertTrue(locations)
        self.assertEqual(len(locations), len(set(locations)), "Sitemap URLs must be unique")
        self.assertTrue(all(url.startswith(LIVE_HOST + "/") for url in locations))
        expected = {
            LIVE_HOST + "/", LIVE_HOST + "/about/",
            LIVE_HOST + "/blog/business-workflow-automation/",
            LIVE_HOST + "/blog/landing-page-conversion/",
            LIVE_HOST + "/blog/seo-guide/",
            LIVE_HOST + "/blog/small-business-website-checklist/",
            LIVE_HOST + "/dashboard/mythos.html",
            LIVE_HOST + "/dashboard/website.html",
            LIVE_HOST + "/pricing/", LIVE_HOST + "/privacy.html",
            LIVE_HOST + "/video-studio.html",
        }
        self.assertEqual(set(locations), expected)
        for excluded in ("/404.html", "/dashboard/login.html", "/dashboard/referrals.html", "/pay.html", "/studio-agent.html"):
            self.assertFalse(any(url.endswith(excluded) for url in locations), excluded)
        robots_text = robots.read_text(encoding="utf-8")
        self.assertIn(LIVE_HOST + "/sitemap.xml", robots_text)
        self.assertIn("Allow: /", robots_text)
        self.assertNotRegex(robots_text, r"(?m)^Disallow:\s*/\s*$")

    def test_upi_checkout_stays_disabled_until_verified(self):
        for relative in ("pay.html", "public-site/pay.html"):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn('const MERCHANT_UPI_ID = "";', source)
            self.assertIn('<button id="pay-button" type="submit" disabled>', source)
            self.assertIn("UPI payment setup pending verification", source)


if __name__ == "__main__":
    unittest.main()
