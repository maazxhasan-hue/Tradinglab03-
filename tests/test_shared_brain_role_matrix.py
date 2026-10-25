import json
import re
import unittest
from pathlib import Path

import shared_brain_role_matrix as role_matrix


class SharedBrainRoleMatrixConfigTests(unittest.TestCase):
    def test_matrix_covers_every_configured_role(self):
        roles_path = Path(__file__).resolve().parents[1] / "company" / "roles.json"
        with roles_path.open("r", encoding="utf-8") as handle:
            departments = json.load(handle)
        expected = list(dict.fromkeys(
            role.strip()
            for department in departments
            for role in department.get("roles", [])
            if isinstance(role, str) and role.strip()
        ))
        self.assertEqual(role_matrix.ROLES, expected)
        self.assertGreaterEqual(len(role_matrix.ROLES), 100)

    def test_every_role_has_a_unique_stable_memory_key(self):
        slugs = [
            re.sub(r"[^a-z0-9]+", "-", role.lower()).strip("-")
            for role in role_matrix.ROLES
        ]
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_every_configured_role_maps_to_an_allowed_identity(self):
        for role in role_matrix.ROLES:
            with self.subTest(role=role):
                identity = role_matrix.agent_id(role)
                self.assertRegex(identity, re.compile(r"^nexora-[a-z0-9._:-]{1,80}$"))
                self.assertLessEqual(len(identity), 87)


if __name__ == "__main__":
    unittest.main()
