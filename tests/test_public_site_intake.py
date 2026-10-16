"""Regression checks for the public TradingLab03 client intake path."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PublicSiteIntakeTests(unittest.TestCase):
    def test_website_has_explicit_manual_instagram_handoff(self):
        html = (ROOT / "dashboard" / "website.html").read_text(encoding="utf-8")
        self.assertIn('id="copyContactBtn"', html)
        self.assertIn('https://www.instagram.com/tradinglab03/', html)
        self.assertIn('window.open("https://www.instagram.com/tradinglab03/"', html)
        self.assertIn("nothing was sent automatically", html)
        self.assertIn("Never include passwords, API keys, or sensitive customer data.", html)

    def test_hq_exposes_delivery_workflow_and_inbox(self):
        html = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
        self.assertIn("autonomous-client-execution.yml", html)
        self.assertIn("https://www.instagram.com/direct/inbox/", html)
        self.assertIn("does not read DMs automatically", html)

if __name__ == "__main__":
    unittest.main()
