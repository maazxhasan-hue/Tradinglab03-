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



    def test_owner_inbox_clears_private_state_when_leaving_page(self):
        html = (ROOT / "dashboard" / "inbox.html").read_text(encoding="utf-8")
        self.assertIn('window.addEventListener("pagehide"', html)
        self.assertIn('keyField.value="";results.replaceChildren();', html)
        self.assertIn('id="adminKey" type="password"', html)

    def test_vercel_security_headers_and_internal_noindex_rules(self):
        import json
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        header_rules = config.get("headers", [])
        all_headers = {
            header["key"].lower(): header["value"]
            for rule in header_rules
            for header in rule.get("headers", [])
        }
        self.assertEqual(all_headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(all_headers.get("x-frame-options"), "DENY")
        self.assertEqual(all_headers.get("referrer-policy"), "strict-origin-when-cross-origin")
        self.assertIn("dashboard", " ".join(rule.get("source", "") for rule in header_rules))
        robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("Disallow: /dashboard/", robots)
        self.assertIn("Disallow: /owner-console/", robots)

if __name__ == "__main__":
    unittest.main()
