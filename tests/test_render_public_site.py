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
        self.assertTrue(all(url.startswith(LIVE_HOST + "/") for url in locations))
        self.assertIn(LIVE_HOST + "/sitemap.xml", robots.read_text(encoding="utf-8"))

    def test_upi_checkout_stays_disabled_until_verified(self):
        for relative in ("pay.html", "public-site/pay.html"):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn('const MERCHANT_UPI_ID = "";', source)
            self.assertIn('<button id="pay-button" type="submit" disabled>', source)
            self.assertIn("UPI payment setup pending verification", source)


if __name__ == "__main__":
    unittest.main()
