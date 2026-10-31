import unittest
from company.operating_controls import Approval, may_execute, can_promote, can_recommend_bonus

class OperatingControlsTests(unittest.TestCase):
    def test_sensitive_action_requires_approval(self):
        self.assertFalse(may_execute(Approval("agent","send_customer_message","lead-1"))[0])
    def test_sensitive_action_needs_separate_approver(self):
        self.assertFalse(may_execute(Approval("agent","submit_bid","job-1",approver="agent",approved=True))[0])
    def test_approved_sensitive_action_can_pass_local_check(self):
        self.assertTrue(may_execute(Approval("agent","deploy_customer_site","client-1",approver="owner",approved=True))[0])
    def test_promotion_requires_evidence(self):
        self.assertFalse(can_promote(completed_tasks=20,quality=99,reliability=99,safety_incidents=0,customer_rating=5)[0])
        self.assertTrue(can_promote(completed_tasks=40,quality=96,reliability=96,safety_incidents=0,customer_rating=4.8)[0])
    def test_safety_incident_blocks_bonus(self):
        self.assertFalse(can_recommend_bonus(completed_tasks=50,quality=99,reliability=99,safety_incidents=1)[0])

if __name__ == "__main__": unittest.main()
