"""Mocked end-to-end acceptance matrix for every registered Nexora agent.

No live AI-provider calls or external side effects are made by this test.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from company.nexora_growth_runtime import AGENT_DIRECTORY, AGENTS, COMPANY_AGENTS, GrowthStore
from company.nexora_agent_executor import execute_agent_draft, role_deliverable_contract


class NexoraAgentAcceptanceMatrixTests(unittest.TestCase):
    def test_full_registry_has_unique_ids_and_nonempty_role_contracts(self):
        all_agents = [*COMPANY_AGENTS, *AGENTS]
        ids = [agent["agent_id"] for agent in all_agents]
        self.assertEqual(len(all_agents), 196)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), set(AGENT_DIRECTORY))
        for agent in all_agents:
            with self.subTest(agent=agent["name"]):
                self.assertTrue(agent["name"].strip())
                self.assertTrue(agent["department"].strip())
                contract = role_deliverable_contract(agent["name"], agent["department"])
                self.assertIsInstance(contract, str)
                self.assertGreater(len(contract.strip()), 40)

    def test_each_registered_agent_completes_mocked_end_to_end_task(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = GrowthStore(Path(temp_dir) / "nexora-agent-matrix.sqlite3")
            fake_env = {"OPENROUTER_API_KEY": "test-only-not-a-real-key"}
            with patch(
                "company.nexora_agent_executor._call_provider",
                return_value="Synthetic acceptance deliverable. Evidence: mocked provider response. Assumptions: test-only.",
            ) as provider:
                for agent in [*COMPANY_AGENTS, *AGENTS]:
                    with self.subTest(agent=agent["name"]):
                        task = store.create_task(
                            title=f"Acceptance test: {agent['name']}",
                            agent_id=agent["agent_id"],
                            inputs={"mode": "acceptance_test", "synthetic": True},
                        )
                        result = execute_agent_draft(store, task["task_id"], environ=fake_env)
                        self.assertEqual(result["status"], "completed")
                        self.assertEqual(result["agent_id"], agent["agent_id"])
                        self.assertTrue(result["outputs"]["draft"].strip())
                        self.assertTrue(result["evidence_refs"])
                        self.assertTrue(result["outputs"]["brain"]["local_memory_saved"])
                        persisted = store.get_task(task["task_id"])
                        self.assertEqual(persisted["status"], "completed")
                        self.assertIn("Synthetic acceptance deliverable", persisted["outputs"]["draft"])
            self.assertEqual(provider.call_count, 196)


if __name__ == "__main__":
    unittest.main()
