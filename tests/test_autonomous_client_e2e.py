import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from company.autonomous_delivery import execute_client_project
from company.specialist_orchestrator import run_specialist_team
from company.tool_agent import run_tool_agent


class AutonomousClientEndToEndTests(unittest.TestCase):
    def test_deterministic_delivery_survives_missing_model_key(self):
        brief = {
            "business_name": "End-to-End Demo Client",
            "service": "business_website",
            "services": ["Website design", "Contact page"],
            "observed_need": "Help local customers understand services and enquire",
            "target_audience": "Local customers",
            "pages_screens_deliverables": ["Home", "Services", "Contact"],
            "version_1_must_have_features": ["Working enquiry form", "Mobile navigation"],
        }
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", {}, clear=True):
            root = Path(tmp)
            delivery = execute_client_project(brief=brief, output_dir=root)
            agent = run_tool_agent(brief=brief, workspace=root, api_key="")
            specialists = run_specialist_team(brief=brief, workspace=root, api_key="")

            self.assertEqual(delivery["status"], "completed_with_limitations")
            self.assertEqual(agent["status"], "skipped_no_api_key")
            self.assertEqual(specialists["status"], "skipped_no_api_key")
            self.assertTrue((root / "delivery_bundle" / "proposal.md").is_file())
            self.assertTrue((root / "delivery_bundle" / "website" / "index.html").is_file())
            self.assertTrue((root / "delivery_bundle" / "website" / "quality_report.json").is_file())
            self.assertTrue((root / "agent_task_plan.md").is_file())
            self.assertTrue((root / "requirement_traceability.csv").is_file())
            self.assertTrue((root / "agent_execution_report.json").is_file())
            specialist_report = json.loads((root / "specialist_execution_report.json").read_text(encoding="utf-8"))
            self.assertEqual(specialist_report["roles_attempted"], len(specialist_report["roles_requested"]))
            self.assertEqual(specialist_report["roles_with_artifact"], 0)
            self.assertFalse(delivery["production_deployment_enabled"])
            self.assertFalse(delivery["sent"])
            self.assertEqual(delivery["verified_revenue"], 0)
            self.assertTrue(all(x["status"] == "needs_implementation_and_acceptance_test"
                                for x in delivery["requirements"] if x["requirement_id"].startswith("FEAT-")))


if __name__ == "__main__":
    unittest.main()
