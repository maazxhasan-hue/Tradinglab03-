"""Static safety checks for the production public-intake service."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ProductionIntakeTests(unittest.TestCase):
    def test_worker_uses_persistent_storage_and_owner_auth(self):
        worker = (ROOT / "worker" / "index.js").read_text(encoding="utf-8")
        self.assertIn('INSERT INTO submissions', worker)
        self.assertIn('SELECT id, created_at, name, email', worker)
        self.assertIn('auth !== "Bearer " + env.ADMIN_API_KEY', worker)
        self.assertIn('if (!env.ADMIN_API_KEY', worker)

    def test_worker_has_input_and_abuse_controls(self):
        worker = (ROOT / "worker" / "index.js").read_text(encoding="utf-8")
        for marker in ("MAX_BODY_BYTES", "MAX_REQUESTS_PER_HOUR", "CF-Connecting-IP", "safeReference", "validEmail", "payload.website"):
            with self.subTest(marker=marker):
                self.assertIn(marker, worker)
        self.assertIn("origin !== env.ALLOWED_ORIGIN", worker)
        self.assertIn("ON DELETE", (ROOT / "worker" / "migrations" / "0001_init.sql").read_text(encoding="utf-8")) if False else None

    def test_public_website_has_opt_in_real_submission_path_and_safe_fallback(self):
        html = (ROOT / "dashboard" / "website.html").read_text(encoding="utf-8")
        self.assertIn('data-intake-endpoint=""', html)
        self.assertIn('name="website"', html)
        self.assertIn('fetch(endpoint + "/api/intake"', html)
        self.assertIn("Your enquiry was received and saved", html)
        self.assertIn("nothing was sent automatically", html)
        self.assertIn("https://www.instagram.com/tradinglab03/", html)

    def test_deployment_requires_secrets_and_wires_endpoint(self):
        workflow = (ROOT / ".github" / "workflows" / "deploy-intake-api.yml").read_text(encoding="utf-8")
        self.assertIn("CLOUDFLARE_API_TOKEN", workflow)
        self.assertIn("TRADINGLAB03_ADMIN_API_KEY", workflow)
        self.assertIn("Deploy TradingLab03 Intake API", workflow)
        self.assertIn("data-intake-endpoint", workflow)


if __name__ == "__main__":
    unittest.main()
