import tempfile
import unittest
from pathlib import Path
from company.website_pipeline import build_from_brief, quality_check


class WebsitePipelineTests(unittest.TestCase):
    def test_build_generates_site_and_quality_report(self):
        brief = {"business_name": "Example Co", "tagline": "Better sites for teams",
                 "services": ["Web design"], "contact_email": "hello@example.com"}
        with tempfile.TemporaryDirectory() as td:
            result = build_from_brief(brief, td)
            self.assertTrue(result["passed"], result["errors"])
            self.assertTrue((Path(td) / "index.html").exists())
            self.assertTrue((Path(td) / "quality_report.json").exists())
            self.assertTrue((Path(td) / "contact.html").exists())
            contact = (Path(td) / "contact.html").read_text(encoding="utf-8")
            self.assertIn('action="mailto:hello@example.com"', contact)
            self.assertIn('name="Message"', contact)
            self.assertIn("opens your email app", contact.lower())
            index = (Path(td) / "index.html").read_text(encoding="utf-8")
            self.assertIn('<details class="mobile-menu">', index)
            self.assertIn("<summary>Menu</summary>", index)
            self.assertTrue(result["checks"][next(i for i, item in enumerate(result["checks"]) if item["name"] == "mobile_navigation_toggle")]["passed"])
            self.assertFalse(result["production_deployment_enabled"])

    def test_requested_pages_and_features_are_rendered_and_checked(self):
        brief = {
            "business_name": "Example Studio", "tagline": "Work made clearer",
            "services": ["Web design"], "contact_email": "hello@example.com",
            "pages_screens_deliverables": ["Home", "About", "Pricing", "Contact"],
            "version_1_must_have_features": ["Accessible enquiry form", "Mobile navigation"],
            "observed_need": "Help customers compare service plans",
            "target_audience": "Small business owners",
            "design_direction_and_references": "Minimal, warm, high contrast",
        }
        with tempfile.TemporaryDirectory() as td:
            result = build_from_brief(brief, td)
            self.assertTrue(result["passed"], result["errors"])
            self.assertTrue((Path(td) / "about.html").exists())
            self.assertTrue((Path(td) / "pricing.html").exists())
            index = (Path(td) / "index.html").read_text()
            self.assertIn("Accessible enquiry form", index)
            self.assertIn("Help customers compare service plans", index)
            manifest = result["manifest"]
            self.assertTrue(manifest["unimplemented_features_require_implementation_and_acceptance_testing"])
            self.assertEqual(manifest["contact_form_mode"], "mailto_handoff")
            contact = (Path(td) / "contact.html").read_text(encoding="utf-8")
            self.assertIn('action="mailto:hello@example.com"', contact)
            self.assertTrue(next(item["passed"] for item in result["checks"] if item["name"] == "contact_form_handoff"))

    def test_missing_optional_copy_is_flagged_not_invented(self):
        brief = {"business_name": "Example Co", "tagline": "",
                 "services": ["Web design"], "contact_email": ""}
        with tempfile.TemporaryDirectory() as td:
            result = build_from_brief(brief, td)
            self.assertTrue(result["passed"], result["errors"])
            index = (Path(td) / "index.html").read_text()
            self.assertIn("Headline to be confirmed with client", index)
            contact = (Path(td) / "contact.html").read_text()
            self.assertIn("Public contact details are pending client approval", contact)
            self.assertEqual(
                result["manifest"]["content_gaps"],
                ["approved_tagline", "approved_public_contact_email"],
            )
            self.assertEqual(result["manifest"]["contact_form_mode"], "not_configured")
            self.assertNotIn("<form", contact)
            self.assertTrue(next(item["passed"] for item in result["checks"] if item["name"] == "contact_form_handoff"))
            self.assertFalse(result["manifest"]["production_scope_complete"])

    def test_unknown_fields_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                build_from_brief({"business_name": "A", "tagline": "B", "services": ["C"], "secret": "no"}, td)

    def test_missing_site_fails(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertFalse(quality_check(td)["passed"])


if __name__ == "__main__":
    unittest.main()
