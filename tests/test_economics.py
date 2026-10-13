import unittest
from datetime import datetime, timezone, timedelta
from botlab.economics import RevenueEvent, BusinessPolicy, evaluate_business, verified_net_revenue
from botlab.dev_team import get_team, release_gate

class EconomicsTests(unittest.TestCase):
    def test_only_verified_nonrefunded_revenue_counts(self):
        self.assertEqual(verified_net_revenue([RevenueEvent(999,True), RevenueEvent(4000,False), RevenueEvent(200,True,True)]), 999)
    def test_shutdown_after_missed_gate(self):
        start = datetime(2026,1,1,tzinfo=timezone.utc)
        d = evaluate_business(started_at=start, now=start+timedelta(days=60), events=[],
            policy=BusinessPolicy())
        self.assertEqual(d.status,"SHUTDOWN")
        self.assertFalse(d.new_jobs_allowed)
        self.assertFalse(d.external_actions_allowed)
    def test_target_keeps_active(self):
        start = datetime(2026,1,1,tzinfo=timezone.utc)
        d = evaluate_business(started_at=start, now=start+timedelta(days=61),
            events=[RevenueEvent(999,True)], policy=BusinessPolicy())
        self.assertEqual(d.status,"ACTIVE")
    def test_team_has_security_redteam(self):
        names = {r["name"] for r in get_team()}
        self.assertIn("Security Engineer",names)
        self.assertIn("Independent Red-Team Reviewer",names)
    def test_release_gate_blocks_without_owner_approval(self):
        ok, blockers = release_gate(tests_pass=True,security_approved=True,owner_approved=False,rollback_ready=True,critical_findings=0)
        self.assertFalse(ok)
        self.assertIn("Owner approval is missing",blockers)

if __name__ == "__main__": unittest.main()
