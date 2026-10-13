import tempfile
import unittest
from pathlib import Path
from company.website_pipeline import build_from_brief, quality_check

class WebsitePipelineTests(unittest.TestCase):
    def test_build_generates_site_and_quality_report(self):
        brief={"business_name":"Example Co","tagline":"Better sites for teams","services":["Web design"],"contact_email":"hello@example.com"}
        with tempfile.TemporaryDirectory() as td:
            result=build_from_brief(brief,td)
            self.assertTrue(result["passed"])
            self.assertTrue((Path(td)/"index.html").exists())
            self.assertTrue((Path(td)/"quality_report.json").exists())
            self.assertFalse(result["production_deployment_enabled"])
    def test_unknown_fields_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                build_from_brief({"business_name":"A","tagline":"B","services":["C"],"secret":"no"},td)
    def test_missing_site_fails(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertFalse(quality_check(td)["passed"])

if __name__ == "__main__": unittest.main()
