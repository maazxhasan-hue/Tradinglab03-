import tempfile, unittest
from company.hiring import CandidateEvidence, evaluate_candidate, promotion_recommendation
from company.projects import ProjectBrief, may_send_proposal
from company.client_voice import CallAuthorization, may_place_call, greeting
from company.website_builder import generate_website

class CompanyTests(unittest.TestCase):
    def test_candidate_not_hired_without_enough_evidence(self):
        d = evaluate_candidate(CandidateEvidence("A","web",99,99,99,99,2))
        self.assertEqual(d.status,"TRIAL")
    def test_candidate_rejected_for_safety_failure(self):
        d = evaluate_candidate(CandidateEvidence("A","web",99,99,99,99,6,1))
        self.assertEqual(d.status,"REJECTED")
    def test_high_performer_can_be_recommended_for_promotion(self):
        d = promotion_recommendation(current_level=1,quality=97,reliability=96,client_rating=4.9,completed_tasks=40,safety_incidents=0)
        self.assertIn("PROMOTION_RECOMMENDED",d)
    def test_call_requires_every_authorization(self):
        self.assertFalse(may_place_call(CallAuthorization(True,True,True,True,False)))
    def test_greeting_discloses_ai(self):
        self.assertIn("AI assistant",greeting())
    def test_proposal_requires_human_approval(self):
        p=ProjectBrief("Client","website","Leads",["Home"],[],"2026-11-01",state="proposal_pending_approval",approved_quote_inr=12000,human_approved=False)
        self.assertFalse(may_send_proposal(p))
    def test_website_generator_escapes_user_content(self):
        with tempfile.TemporaryDirectory() as d:
            out=generate_website(output_dir=d,business_name="<script>alert(1)</script>",tagline="Great site",services=["Web design"],contact_email="hello@example.com")
            page=(out/"index.html").read_text()
            self.assertNotIn("<script>alert(1)</script>",page)
            self.assertIn("Web design",page)

if __name__ == "__main__": unittest.main()
