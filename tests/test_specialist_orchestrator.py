import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from company.specialist_orchestrator import run_specialist_team


class SpecialistOrchestratorTests(unittest.TestCase):
    def brief(self):
        return {
            "business_name": "Example",
            "service": "landing_page",
            "services": ["Website design"],
            "observed_need": "Explain services and collect enquiries",
        }

    def test_no_key_records_roles_without_calling_model(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", {}, clear=True):
            with patch("company.specialist_orchestrator.run_tool_agent") as agent:
                report = run_specialist_team(brief=self.brief(), workspace=tmp, api_key="")
        agent.assert_not_called()
        self.assertEqual(report["status"], "skipped_no_api_key")
        self.assertGreater(report["roles_attempted"], 1)
        self.assertTrue((Path(tmp) / "specialist_execution_report.json").is_file())

    def test_role_passes_are_sequential_and_artifacts_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            def fake_agent(*, brief, workspace, api_key, max_rounds):
                rel = brief["specialist_execution"]["required_artifact"]
                path = Path(workspace) / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("Evidence and remaining checks", encoding="utf-8")
                return {"status": "completed", "tool_calls": 1, "final_message": "done"}
            with patch("company.specialist_orchestrator.run_tool_agent", side_effect=fake_agent) as agent:
                report = run_specialist_team(brief=self.brief(), workspace=tmp, api_key="test-key")
        self.assertEqual(agent.call_count, len(report["roles_requested"]))
        self.assertEqual(report["roles_with_artifact"], len(report["roles_requested"]))
        self.assertEqual(report["status"], "completed_with_limitations")
        saved = json.loads((Path(tmp) / "specialist_execution_report.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["roles_attempted"], len(report["roles_requested"]))

    def test_stops_after_provider_failure_and_keeps_partial_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("company.specialist_orchestrator.run_tool_agent", return_value={
                "status": "unavailable", "tool_calls": 0, "error": "quota"
            }) as agent:
                report = run_specialist_team(brief=self.brief(), workspace=tmp, api_key="test-key")
        self.assertEqual(agent.call_count, 1)
        self.assertEqual(report["status"], "partial_or_unavailable")
        self.assertEqual(report["roles_attempted"], 1)

    def test_rejects_unsupported_service_and_excessive_rounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Unsupported service"):
                run_specialist_team(brief={**self.brief(), "service": "magic"}, workspace=tmp, api_key="")
            with self.assertRaisesRegex(ValueError, "between 1 and 3"):
                run_specialist_team(brief=self.brief(), workspace=tmp, api_key="", max_rounds_per_role=4)


if __name__ == "__main__":
    unittest.main()
