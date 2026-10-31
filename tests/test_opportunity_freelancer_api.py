import sys
import types
import unittest
from unittest.mock import patch

from company.freelancer_api_source import fetch_projects
from company.opportunity_scout import score_listing


class FreelancerApiSourceTests(unittest.TestCase):
    def _fake_sdk(self, response):
        session_module = types.ModuleType("freelancersdk.session")
        class Session:
            def __init__(self, oauth_token):
                self.oauth_token = oauth_token
        session_module.Session = Session

        projects_module = types.ModuleType("freelancersdk.resources.projects.projects")
        calls = {}
        def search_projects(session, **kwargs):
            calls["token"] = session.oauth_token
            calls["kwargs"] = kwargs
            return response
        projects_module.search_projects = search_projects

        package = types.ModuleType("freelancersdk")
        package.__path__ = []
        resources = types.ModuleType("freelancersdk.resources")
        resources.__path__ = []
        projects_pkg = types.ModuleType("freelancersdk.resources.projects")
        projects_pkg.__path__ = []
        return {
            "freelancersdk": package,
            "freelancersdk.session": session_module,
            "freelancersdk.resources": resources,
            "freelancersdk.resources.projects": projects_pkg,
            "freelancersdk.resources.projects.projects": projects_module,
        }, calls

    def test_maps_official_sdk_results_to_unverified_leads(self):
        modules, calls = self._fake_sdk({"result": {"projects": [{
            "id": 123, "title": "Website redesign for small business",
            "description": "Paid fixed-price project for a WordPress website",
            "seo_url": "https://www.freelancer.com/projects/wordpress/website-redesign"
        }]}})
        with patch.dict(sys.modules, modules):
            rows = fetch_projects({"name": "Freelancer API", "limit": 500, "query": "website"}, "secret-token", score_listing)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], "https://www.freelancer.com/projects/wordpress/website-redesign")
        self.assertFalse(rows[0]["paid_contract_verified"])
        self.assertEqual(rows[0]["status"], "new_lead")
        self.assertEqual(calls["token"], "secret-token")
        self.assertEqual(calls["kwargs"]["limit"], 100)
        self.assertTrue(calls["kwargs"]["active_only"])

    def test_rejects_non_https_and_missing_urls(self):
        modules, _ = self._fake_sdk({"projects": [
            {"title": "Unsafe project", "url": "http://example.com/project"},
            {"title": "Missing URL"},
            {"title": "Safe project", "url": "https://www.freelancer.com/projects/123/safe"}
        ]})
        with patch.dict(sys.modules, modules):
            rows = fetch_projects({"name": "Freelancer API", "limit": 10}, "secret-token", score_listing)
        self.assertEqual([row["title"] for row in rows], ["Safe project"])

    def test_invalid_response_shape_fails_closed(self):
        modules, _ = self._fake_sdk({"unexpected": "shape"})
        with patch.dict(sys.modules, modules):
            with self.assertRaisesRegex(ValueError, "did not contain a project list"):
                fetch_projects({"name": "Freelancer API"}, "secret-token", score_listing)

if __name__ == "__main__":
    unittest.main()
