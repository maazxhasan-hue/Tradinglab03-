import re
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
        self.assertIn(r""".replace(/"/g,'""')""", self.html)
        self.assertRegex(self.html, r""".replace\(/\[[^\]]*\\r[^\]]*\\n[^\]]*\]\+/g,' '\)""")

    def test_proposal_draft_requires_input_and_is_not_sent(self):
        self.assertIn("if(!business||!need)", self.html)
        self.assertIn("Nothing was uploaded, sent, or marked as revenue.", self.html)
        self.assertIn("Draft for human review — not sent or accepted", self.html)
        self.assertIn("qpOutput.value=quickProposalText", self.html)

    def test_proposal_website_requires_https(self):
        self.assertIn('id="qpWebsite" type="url"', self.html)
        self.assertIn("Website must use HTTPS, or leave it blank.", self.html)
        self.assertIn("test(website)", self.html)

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


    def test_client_projects_are_prioritized_and_categories_stay_separate(self):
        self.assertIn("function leadKind(x)", self.html)
        self.assertIn("return kind==='client_project';if(leadFilter.value==='freelance')return kind==='freelance_work';", self.html)
        self.assertIn("kindRank(a)-kindRank(b)||reviewRank(a)-reviewRank(b)", self.html)

    def test_review_mark_is_not_misrepresented_as_verification(self):
        self.assertIn("Reviewed in this browser", self.html)
        self.assertIn("Not reviewed in this browser", self.html)
        self.assertIn("Human verification pending", self.html)
        self.assertIn("It does not verify the lead or payment.", self.html)

    def test_lead_review_shows_evidence_and_ranks_higher_scores_first(self):
        self.assertIn("Number(b.opportunity_score||0)-Number(a.opportunity_score||0)", self.html)
        self.assertIn("'Scout score '+Number(x.opportunity_score)", self.html)
        self.assertIn("recorded signal", self.html)
        self.assertIn("Review flags: ", self.html)

    def test_lead_qualification_checklist_is_local_and_exported(self):
        self.assertIn("const QUAL_KEY='tradinglab03_hq_lead_qualification_v1'", self.html)
        self.assertIn("Listing is still open", self.html)
        self.assertIn("Buyer need and intent checked", self.html)
        self.assertIn("Budget and payment terms checked", self.html)
        self.assertIn("localStorage.setItem(QUAL_KEY,JSON.stringify(qualification))", self.html)
        self.assertIn("'qualification_checks'", self.html)
        self.assertIn("not proof of legitimacy or payment", self.html)

    def test_client_lead_can_prefill_local_proposal_draft(self):
        self.assertIn("prepare.textContent='Prepare proposal draft'", self.html)
        self.assertIn("prepare.disabled=kind!=='client_project'", self.html)
        self.assertIn("Public listing: ", self.html)
        self.assertIn("Lead details copied locally into the proposal form.", self.html)
        self.assertIn("nothing was sent.", self.html)


    def test_proposal_quality_review_is_local_and_covers_core_terms(self):
        self.assertIn('id="qpQuality"', self.html)
        self.assertIn('id="qpQualityReport"', self.html)
        self.assertIn("function reviewProposalQuality(text)", self.html)
        self.assertIn("Scope and deliverables", self.html)
        self.assertIn("Price or quote decision", self.html)
        self.assertIn("Timeline and milestones", self.html)
        self.assertIn("Buyer evidence", self.html)
        self.assertIn("Potential unsupported claim", self.html)
        self.assertIn("Heuristic checks only", self.html)
        self.assertIn("qpQuality.disabled=false", self.html)

    def test_quality_review_does_not_claim_to_verify_facts_or_send_proposals(self):
        self.assertIn("this does not verify facts, legal terms, pricing, or buyer legitimacy", self.html)
        self.assertIn("qpQuality.addEventListener('click'", self.html)
        script = self.html.split("<script>", 1)[1].split("</script>", 1)[0]
        self.assertNotIn("fetch(", script)
        self.assertNotIn("sendBeacon(", script)

if __name__ == "__main__":
    unittest.main()
