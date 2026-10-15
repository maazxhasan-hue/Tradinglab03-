import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard" / "index.html"


class DashboardRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = DASHBOARD.read_text(encoding="utf-8")

    def test_dashboard_is_standalone_and_has_expected_sections(self):
        self.assertIn("<!doctype html>", self.html.lower())
        for section in ('id="quickProposal"', 'id="leadReview"', 'id="projectForm"'):
            with self.subTest(section=section):
                self.assertIn(section, self.html)

    def test_csv_export_uses_real_crlf_line_endings(self):
        self.assertIn(".join('\\r\\n');const blob=new Blob([csv]", self.html)
        self.assertNotIn(".join('\\\\r\\\\n');const blob=new Blob([csv]", self.html)

    def test_csv_cells_escape_quotes_and_sanitize_line_breaks(self):
        self.assertIn(".replace(/\\"/g,'\\"\\"')", self.html)
        self.assertIn(".replace(/[\\r\\n]+/g,' ')", self.html)

    def test_proposal_draft_requires_input_and_is_not_sent(self):
        self.assertIn("if(!business||!need)", self.html)
        self.assertIn("Nothing was uploaded, sent, or marked as revenue.", self.html)
        self.assertIn("Draft for human review — not sent or accepted", self.html)
        self.assertIn("qpOutput.value=quickProposalText", self.html)

    def test_proposal_website_requires_https(self):
        self.assertIn("if(website&&!/^https:\\/\\/\\//i.test(website))", self.html)
        self.assertIn("Website must use HTTPS, or leave it blank.", self.html)

    def test_clipboard_api_has_manual_copy_fallback(self):
        self.assertIn("navigator.clipboard.writeText(quickProposalText)", self.html)
        self.assertIn("Select the preview text and copy it manually.", self.html)

    def test_project_and_review_data_are_local_only(self):
        self.assertIn("localStorage.setItem(STORAGE_KEY,JSON.stringify(projects))", self.html)
        self.assertIn("localStorage.setItem(REVIEW_KEY,JSON.stringify(reviewedIds))", self.html)
        self.assertIn("Nothing was uploaded, contacted, or marked as paid.", self.html)

    def test_no_automatic_submission_or_network_request_in_dashboard_script(self):
        script = self.html.split("<script>", 1)[1].split("</script>", 1)[0]
        self.assertNotIn("fetch(", script)
        self.assertNotIn("XMLHttpRequest", script)
        self.assertNotIn("sendBeacon(", script)


if __name__ == "__main__":
    unittest.main()
