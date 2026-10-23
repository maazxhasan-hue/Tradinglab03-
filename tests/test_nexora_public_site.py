"""Regression checks for Nexora's public business offer and referral links."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LIVE_HOST = "https://nexora-ai-public.pages.dev"

class NexoraPublicSiteTests(unittest.TestCase):
    def test_homepage_describes_the_real_business_services(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for phrase in ("Trading courses", "Business websites", "Landing pages", "AI tools", "Refer &amp; Earn"):
            self.assertIn(phrase, html)
        self.assertIn('href="/dashboard/referrals.html"', html)
        self.assertIn("trading profits are never guaranteed", html)

    def test_public_metadata_uses_current_cloudflare_pages_host_and_same_origin_consent_script(self):
        for path in ("index.html", "dashboard/website.html"):
            html = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn(LIVE_HOST, html)
            self.assertNotIn("nexora-ai-public.onrender.com", html)
            self.assertNotIn("nexora-ai-public.netlify.app", html)
            self.assertNotIn("nexora-ai-sooty-two.vercel.app", html)
        for path in ("index.html", "dashboard/website.html", "dashboard/login.html", "dashboard/privacy.html"):
            html = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn('src="/dashboard/analytics-consent.js"', html)
            self.assertNotIn("nexora-ai-public.netlify.app/dashboard/analytics-consent.js", html)

    def test_referral_terms_do_not_promise_unapproved_commissions(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("approved terms", html)
        self.assertIn("No fixed reward, payout date, or commission rate is promised", html)
        worker = (ROOT / "worker" / "index.js").read_text(encoding="utf-8")
        self.assertIn(LIVE_HOST + '/dashboard/login.html?mode=signup&ref=', worker)
        self.assertIn("Referral rewards are not guaranteed.", worker)

if __name__ == "__main__":
    unittest.main()
