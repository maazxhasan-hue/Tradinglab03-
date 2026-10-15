import csv
import tempfile
import unittest
from pathlib import Path

from company.autonomous_delivery import execute_client_project


class AutonomousDeliveryTests(unittest.TestCase):
    def brief(self, service="business_website"):
        return {
            "business_name": "Example Client",
            "services": ["Website design", "Contact page"],
            "service": service,
            "observed_need": "Help customers understand services and contact the business",
            "target_audience": "Local customers",
            "pages_screens_deliverables": ["Home", "Services", "Contact"],
            "version_1_must_have_features": ["Working enquiry form", "Mobile navigation"],
            "future_features_backlog": ["Customer portal"],
        }

    def test_executes_supported_delivery_and_emits_traceability(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = execute_client_project(brief=self.brief(), output_dir=tmp)
            root = Path(tmp)
            self.assertEqual(report["status"], "completed_with_limitations")
            self.assertTrue((root / "agent_task_plan.md").is_file())
            self.assertTrue((root / "requirement_traceability.csv").is_file())
            self.assertTrue((root / "agent_execution_report.json").is_file())
            self.assertTrue((root / "delivery_bundle" / "proposal.md").is_file())
            self.assertTrue((root / "delivery_bundle" / "website" / "index.html").is_file())
            self.assertFalse(report["production_deployment_enabled"])
            self.assertFalse(report["sent"])
            self.assertEqual(report["verified_revenue"], 0)
            self.assertEqual(report["counts"]["needs_implementation_and_acceptance_test"], 2)
            rows = list(csv.DictReader((root / "requirement_traceability.csv").open(encoding="utf-8")))
            self.assertEqual(len(rows), 5)
            self.assertTrue(any(row["status"] == "needs_implementation_and_acceptance_test" for row in rows))

    def test_service_specific_draft_is_generated_for_each_supported_service(self):
        expected = {
            "business_website": "website_implementation_notes.md",
            "landing_page": "website_implementation_notes.md",
            "website_audit": "website_audit_plan.md",
            "seo_content": "seo_content_draft.md",
            "short_video": "short_video_package.md",
            "business_automation": "automation_design.md",
        }
        for service, artifact in expected.items():
            with self.subTest(service=service), tempfile.TemporaryDirectory() as tmp:
                report = execute_client_project(brief=self.brief(service), output_dir=tmp)
                self.assertIn(artifact, report["service_artifacts"])
                self.assertTrue((Path(tmp) / artifact).is_file())
                self.assertTrue(report["roles_assigned"])

    def test_missing_material_brief_fields_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "business_name"):
                execute_client_project(brief={}, output_dir=tmp)

    def test_unsupported_service_is_not_silently_accepted(self):
        brief = self.brief("unlimited_magic")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Unsupported service"):
                execute_client_project(brief=brief, output_dir=tmp)


if __name__ == "__main__":
    unittest.main()
