import sys
import types
import unittest
from unittest.mock import patch

from company.freelancer_api_source import fetch_projects
from company.opportunity_scout import score_listing


def sdk_modules(response, capture=None):
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
    return {
        "freelancersdk": types.ModuleType("freelancersdk"),
        "freelancersdk.session": session_module,
        "freelancersdk.resources": types.ModuleType("freelancersdk.resources"),
        "freelancersdk.resources.projects": types.ModuleType("freelancersdk.resources.projects"),
        "freelancersdk.resources.projects.projects": projects_module,
    }


class FreelancerApiSourceTests(unittest.TestCase):
    def test_maps_api_projects_to_unverified_leads(self):
        response = {"result": {"projects": [{
            "id": 12345, "title": "Need a website redesign",
            "seo_url": "https://www.freelancer.com/projects/12345",
            "description": "<p>I need a new website for my business and can pay for the project.</p>",
            "time_submitted": 1720000000,
        }]}}
        with patch.dict(sys.modules, sdk_modules(response)):
            rows = fetch_projects({"name": "Freelancer.com API", "limit": 10, "query": "website"}, "test-token", score_listing)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], "https://www.freelancer.com/projects/12345")
        self.assertTrue(rows[0]["client_fit"])
        self.assertFalse(rows[0]["paid_contract_verified"])
        self.assertEqual(rows[0]["status"], "new_lead")
        self.assertIn("Human verifies", rows[0]["next_step"])

    def test_uses_bounded_limit_and_read_only_search(self):
        capture = {}
        with patch.dict(sys.modules, sdk_modules({"projects": []}, capture)):
            rows = fetch_projects({"name": "Freelancer.com API", "limit": 999, "query": "wordpress"}, "test-token", score_listing)
        self.assertEqual(rows, [])
        self.assertEqual(capture["token"], "test-token")
        self.assertEqual(capture["kwargs"]["limit"], 100)
        self.assertEqual(capture["kwargs"]["offset"], 0)
        self.assertTrue(capture["kwargs"]["active_only"])
        self.assertEqual(set(capture["kwargs"]), {"query", "limit", "offset", "active_only"})

    def test_rejects_unexpected_response_shape(self):
        with patch.dict(sys.modules, sdk_modules({"unexpected": "shape"})):
            with self.assertRaisesRegex(ValueError, "did not contain a project list"):
                fetch_projects({"name": "Freelancer.com API"}, "test-token", score_listing)

    def test_ignores_projects_without_title_or_safe_url(self):
        response = {"projects": [
            {"id": 1, "title": "No safe URL", "url": "http://example.com"},
            {"id": 2, "title": ""},
        ]}
        with patch.dict(sys.modules, sdk_modules(response)):
            self.assertEqual(fetch_projects({"name": "Freelancer.com API"}, "test-token", score_listing), [])


if __name__ == "__main__":
    unittest.main()
