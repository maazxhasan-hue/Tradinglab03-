import sys
import types
import unittest
from unittest.mock import patch

from company.freelancer_api_source import fetch_projects
from company.opportunity_scout import score_listing


class FreelancerApiSourceTests(unittest.TestCase):
    def _install_sdk(self, response, capture=None):
        session_module = types.ModuleType("freelancersdk.session")
        class Session:
            def __init__(self, oauth_token):
                if capture is not None:
                    capture["token"] = oauth_token
        session_module.Session = Session

        projects_module = types.ModuleType("freelancersdk.resources.projects.projects")
        def search_projects(session, **kwargs):
            if capture is not None:
                capture["kwargs"] = kwargs
            return response
        projects_module.search_projects = search_projects

        root_module = types.ModuleType("freelancersdk")
        resources_module = types.ModuleType("freelancersdk.resources")
        projects_parent = types.ModuleType("freelancersdk.resources.projects")
        with patch.dict(sys.modules, {
            "freelancersdk": root_module,
            "freelancersdk.session": session_module,
            "freelancersdk.resources": resources_module,
            "freelancersdk.resources.projects": projects_parent,
            "freelancersdk.resources.projects.projects": projects_module,
        }):
            return fetch_projects

    def test_maps_api_projects_to_unverified_leads(self):
        response = {"result": {"projects": [{
            "id": 12345,
            "title": "Need a website redesign",
            "description": "<p>I need a new website for my business and can pay for the project.</p>",
            "time_submitted": 1720000000,
        }]}}
        fetch = self._install_sdk(response)
        rows = fetch(
            {"name": "Freelancer.com API", "limit": 10, "query": "website"},
            "test-token",
            score_listing,
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], "https://www.freelancer.com/projects/12345")
        self.assertTrue(rows[0]["client_fit"])
        self.assertFalse(rows[0]["paid_contract_verified"])
        self.assertEqual(rows[0]["status"], "new_lead")
        self.assertIn("Human verifies", rows[0]["next_step"])

    def test_uses_bounded_limit_and_never_bids_or_messages(self):
        capture = {}
        fetch = self._install_sdk({"projects": []}, capture)
        rows = fetch(
            {"name": "Freelancer.com API", "limit": 999, "query": "wordpress"},
            "test-token",
            score_listing,
        )
        self.assertEqual(rows, [])
        self.assertEqual(capture["token"], "test-token")
        self.assertEqual(capture["kwargs"]["limit"], 100)
        self.assertEqual(capture["kwargs"]["offset"], 0)
        self.assertTrue(capture["kwargs"]["active_only"])
        self.assertEqual(set(capture["kwargs"]), {"query", "limit", "offset", "active_only"})

    def test_rejects_unexpected_response_shape(self):
        fetch = self._install_sdk({"unexpected": "shape"})
        with self.assertRaisesRegex(ValueError, "did not contain a project list"):
            fetch({"name": "Freelancer.com API"}, "test-token", score_listing)

    def test_ignores_projects_without_title_or_safe_url(self):
        fetch = self._install_sdk({"projects": [
            {"id": 1, "title": "No safe URL", "url": "http://example.com"},
            {"id": 2, "title": ""},
        ]})
        self.assertEqual(fetch({"name": "Freelancer.com API"}, "test-token", score_listing), [])


if __name__ == "__main__":
    unittest.main()
