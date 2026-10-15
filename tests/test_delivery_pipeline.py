import json
import tempfile
import unittest
from pathlib import Path

from company.delivery_pipeline import run_delivery


class DeliveryPipelineTests(unittest.TestCase):
    def test_end_to_end_bundle_contains_proposal_website_and_honest_report(self):
        brief = {
            "business_name": "Example Cafe",
            "tagline": "Coffee and conversation",
            "services": ["Cafe menu", "Contact details"],
            "contact_email": "hello@example.com",
            "service": "business_website",
            "observed_need": "The provided brief requests a menu and contact page",
            "evidence": "Operator-provided test brief",
        }
        with tempfile.TemporaryDirectory() as tmp:
            report = run_delivery(brief=brief, output_dir=tmp)
            root = Path(tmp)
            self.assertEqual(report["status"], "ready_for_human_review")
            self.assertTrue((root / "proposal.md").is_file())
            self.assertTrue((root / "proposal.json").is_file())
            self.assertTrue((root / "website" / "index.html").is_file())
            self.assertTrue((root / "website" / "quality_report.json").is_file())
            self.assertFalse(report["sent"])
            self.assertFalse(report["production_deployment_enabled"])
            self.assertEqual(report["verified_revenue"], 0)
            self.assertIn("not sent or accepted", (root / "proposal.md").read_text())
            saved = json.loads((root / "delivery_report.json").read_text())
            self.assertEqual(saved["status"], "ready_for_human_review")

    def test_requires_complete_brief(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Missing required brief fields"):
                run_delivery(brief={"business_name": "Incomplete"}, output_dir=tmp)

    def test_rejects_unknown_service(self):
        brief = {
            "business_name": "Example", "tagline": "Tagline",
            "services": ["Web"], "contact_email": "hello@example.com",
            "observed_need": "Test need", "service": "guaranteed_money",
        }
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Unsupported proposal service"):
                run_delivery(brief=brief, output_dir=tmp)



    def test_saved_lead_can_feed_delivery_only_when_classified_as_client_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = root / "leads.json"
            store.write_text(json.dumps({"leads": [{
                "id": "TL-CLIENT", "business_name": "Example Cafe",
                "service": "business_website", "need": "Needs a menu page",
                "website_url": "https://example.com", "source_url": "https://source.example/project",
                "evidence": "Public listing, unverified",
                "opportunity_type": "client_project", "client_fit": True,
            }]}), encoding="utf-8")
            brief = {
                "lead_id": "TL-CLIENT", "business_name": "Example Cafe",
                "tagline": "Coffee and conversation", "services": ["Menu page"],
                "contact_email": "hello@example.com", "service": "business_website",
            }
            report = run_delivery(brief=brief, output_dir=root / "bundle", lead_store=store)
            self.assertEqual(report["status"], "ready_for_human_review")
            self.assertIn("Needs a menu page", (root / "bundle" / "proposal.md").read_text())

    def test_saved_freelance_listing_is_not_accepted_as_client_lead(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = root / "leads.json"
            store.write_text(json.dumps({"leads": [{
                "id": "TL-FREELANCE", "business_name": "Contract role",
                "service": "business_website", "need": "Apply for job",
                "opportunity_type": "freelance_work", "client_fit": False,
            }]}), encoding="utf-8")
            brief = {
                "lead_id": "TL-FREELANCE", "business_name": "Contract role",
                "tagline": "Tagline", "services": ["Web"], "contact_email": "hello@example.com",
                "service": "business_website",
            }
            with self.assertRaisesRegex(ValueError, "explicitly classified as a client_project"):
                run_delivery(brief=brief, output_dir=root / "bundle", lead_store=store)

    def test_legacy_lead_with_client_fit_flag_but_no_client_project_type_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = root / "leads.json"
            store.write_text(json.dumps({"leads": [{
                "id": "TL-LEGACY-JOB", "business_name": "Freelance Copywriter",
                "service": "seo_content", "need": "A freelance job vacancy, not a buyer request",
                "source_url": "https://example.invalid/job", "evidence": "Legacy imported listing",
                "client_fit": True,
            }]}), encoding="utf-8")
            brief = {
                "lead_id": "TL-LEGACY-JOB", "business_name": "Freelance Copywriter",
                "tagline": "Draft only", "services": ["Content"], "contact_email": "review@example.invalid",
                "service": "seo_content",
            }
            with self.assertRaisesRegex(ValueError, "explicitly classified as a client_project"):
                run_delivery(brief=brief, output_dir=root / "bundle", lead_store=store)

if __name__ == "__main__":
    unittest.main()
