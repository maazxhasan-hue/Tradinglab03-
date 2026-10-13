import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class DepartmentRegistryTests(unittest.TestCase):
    def test_required_departments_present(self):
        data=json.loads((ROOT/"company"/"departments.json").read_text(encoding="utf-8"))
        names={d["name"] for d in data["departments"]}
        required={"Marketing & Brand","Quality, Audit & Testing","Research & Analysis",
                  "Creative & Presenting","Builders & Engineering","Customer Success & CA",
                  "Finance, Legal & Procurement","People & Agent Operations","IT, Security & Data"}
        self.assertTrue(required.issubset(names))
    def test_every_department_has_mission_and_teams(self):
        data=json.loads((ROOT/"company"/"departments.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data["departments"]),12)
        for dept in data["departments"]:
            self.assertTrue(dept["mission"])
            self.assertTrue(dept["teams"])

if __name__ == "__main__": unittest.main()
