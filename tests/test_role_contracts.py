import unittest

from company.nexora_growth_runtime import AGENT_DIRECTORY
from company.role_contracts import all_role_contracts, role_contract, validate_role_contract


class RoleContractTests(unittest.TestCase):
    def test_every_registered_agent_has_a_valid_contract(self):
        contracts = all_role_contracts()
        self.assertEqual(len(contracts), len(AGENT_DIRECTORY))
        self.assertEqual({item["agent_id"] for item in contracts}, set(AGENT_DIRECTORY))
        for contract in contracts:
            with self.subTest(agent_id=contract["agent_id"]):
                self.assertEqual(validate_role_contract(contract), [])

    def test_unknown_agent_fails_closed(self):
        with self.assertRaises(KeyError):
            role_contract("not-a-real-agent")

    def test_external_actions_default_to_disabled(self):
        for contract in all_role_contracts():
            self.assertIs(contract["external_actions_enabled"], False)
            self.assertEqual(contract["completion_policy"], "needs_review")

    def test_contracts_define_real_deliverables_and_quality_checks(self):
        for contract in all_role_contracts():
            self.assertGreaterEqual(len(contract["deliverables"]), 3)
            self.assertGreaterEqual(len(contract["quality_checks"]), 2)
            self.assertTrue(contract["mission"].strip())


if __name__ == "__main__":
    unittest.main()
