import unittest
from botlab.policy import review_content, require_approval
from botlab.workflow import build_reel_draft
from botlab.knowledge import answer_faq

class PolicyTests(unittest.TestCase):
    def test_guaranteed_profit_flagged(self):
        self.assertTrue(review_content("This gives guaranteed profits"))
    def test_approval_required(self):
        self.assertTrue(require_approval("approved"))
        self.assertFalse(require_approval("pending_approval"))
    def test_draft_not_published(self):
        d = build_reel_draft("backtesting basics")
        self.assertEqual(d["state"], "pending_approval")
        self.assertFalse(d["external_publish_enabled"])
    def test_unknown_faq_escalates(self):
        self.assertIn("escalate", answer_faq("Can you customize my account?").lower())
    def test_price_faq(self):
        self.assertIn("₹999", answer_faq("What is the price?"))

if __name__ == "__main__": unittest.main()
