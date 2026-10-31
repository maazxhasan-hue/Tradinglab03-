import tempfile, unittest
from botlab.orchestrator import LocalOrchestrator

class OrchestratorTests(unittest.TestCase):
    def test_duplicate_jobs_are_idempotent_and_transition_is_guarded(self):
        with tempfile.TemporaryDirectory() as d:
            o = LocalOrchestrator(d + "/state.json")
            a = o.enqueue("reel", {"topic":"backtesting"})
            b = o.enqueue("reel", {"topic":"backtesting"})
            self.assertEqual(a.job_id,b.job_id)
            o.transition(a.job_id,"in_progress")
            o.transition(a.job_id,"pending_approval")
            with self.assertRaises(ValueError):
                o.transition(a.job_id,"published")

if __name__ == "__main__": unittest.main()
