"""Regression checks for the public TradingLab03 client intake path."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PublicSiteIntakeTests(unittest.TestCase):
    def test_website_requires_client_sign_in_before_project_submission(self):
        html = (ROOT / "dashboard" / "website.html").read_text(encoding="utf-8")
        self.assertIn('href="login.html?next=website.html%23project">Log in', html)
        self.assertIn('href="login.html?mode=signup&next=website.html%23project">Sign up to build', html)
        self.assertIn('localStorage.getItem("nexora_client_token")', html)
        self.assertIn('"/api/auth/"+(mode==="login"?"login":"register")', (ROOT / "dashboard" / "login.html").read_text(encoding="utf-8"))
        self.assertIn("Never include passwords, API keys, or sensitive customer data.", html)

    def test_hq_exposes_delivery_workflow_and_inbox(self):
        html = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
        self.assertIn("autonomous-client-execution.yml", html)
        self.assertIn("https://www.instagram.com/direct/inbox/", html)
        self.assertIn("DMs are not read or sent automatically", html)

if __name__ == "__main__":
    unittest.main()
