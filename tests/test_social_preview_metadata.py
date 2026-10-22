"""Static regression checks for public-page social preview metadata and image alt text."""

from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public-site"
BASE = "https://nexora-ai-public.onrender.com"
PAGES = [
    "index.html", "about/index.html", "pricing/index.html", "privacy.html",
    "video-studio.html", "dashboard/website.html", "dashboard/mythos.html",
    "blog/seo-guide/index.html",
    "blog/small-business-website-checklist/index.html",
    "blog/landing-page-conversion/index.html",
    "blog/business-workflow-automation/index.html",
    "dashboard/login.html", "dashboard/referrals.html", "dashboard/privacy.html",
    "pay.html", "studio-agent.html", "404.html",
]


class PageAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.images = []
        self.title_depth = 0
        self.title_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            key = attrs.get("property") or attrs.get("name")
            if key:
                self.meta.setdefault(key, []).append(attrs.get("content", ""))
        elif tag == "img":
            self.images.append(attrs)
        elif tag == "title":
            self.title_depth += 1

    def handle_endtag(self, tag):
        if tag == "title" and self.title_depth:
            self.title_depth -= 1

    def handle_data(self, data):
        if self.title_depth:
            self.title_text.append(data)


class SocialPreviewMetadataTests(unittest.TestCase):
    def test_all_pages_have_required_unique_social_metadata(self):
        for relative in PAGES:
            with self.subTest(page=relative):
                parser = PageAudit()
                parser.feed((PUBLIC / relative).read_text(encoding="utf-8"))
                for key in (
                    "og:title", "og:description", "og:type", "og:url", "og:image",
                    "twitter:card", "twitter:title", "twitter:description", "twitter:image",
                ):
                    self.assertEqual(len(parser.meta.get(key, [])), 1, f"{relative}: expected one {key}")
                    self.assertTrue(parser.meta[key][0].strip(), f"{relative}: empty {key}")
                self.assertEqual(parser.meta["twitter:card"][0], "summary_large_image")
                self.assertEqual(parser.meta["og:image"][0], f"{BASE}/og-image.svg")
                self.assertEqual(parser.meta["twitter:image"][0], f"{BASE}/og-image.svg")
                self.assertEqual(parser.meta["og:image:width"][0], "1200")
                self.assertEqual(parser.meta["og:image:height"][0], "630")
                self.assertTrue(parser.meta["og:url"][0].startswith(BASE + "/"))

    def test_no_inline_images_without_alt_text(self):
        for relative in PAGES:
            with self.subTest(page=relative):
                parser = PageAudit()
                parser.feed((PUBLIC / relative).read_text(encoding="utf-8"))
                for image in parser.images:
                    self.assertIn("alt", image, f"{relative}: image missing alt attribute")
                    self.assertIsNotNone(image["alt"], f"{relative}: image alt must not be null")

    def test_default_share_image_declares_1200_by_630(self):
        svg = (PUBLIC / "og-image.svg").read_text(encoding="utf-8")
        self.assertRegex(svg, r'<svg[^>]*\bwidth="1200"')
        self.assertRegex(svg, r'<svg[^>]*\bheight="630"')


if __name__ == "__main__":
    unittest.main()
