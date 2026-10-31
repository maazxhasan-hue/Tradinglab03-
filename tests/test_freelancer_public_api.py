import json
import unittest
from unittest.mock import patch

from company.freelancer_api_source import fetch_public_projects
from company.opportunity_scout import score_listing


class FreelancerPublicApiTests(unittest.TestCase):
    def test_public_endpoint_parses_active_projects_without_token(self):
        payload = {
            "status": "success",
            "result": {
                "projects": [{
                    "id": 12345,
                    "title": "Need a business website redesign",
                    "seo_url": "website-design",
                    "description": "Our small business needs a website. Looking for a freelancer to redesign it.",
                    "time_submitted": 1720000000,
                }]
            }
        }

        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit): return json.dumps(payload).encode()

        with patch("company.freelancer_api_source.urlopen", return_value=Response()) as mocked:
            rows = fetch_public_projects(
                {"name": "Freelancer.com - free public API", "limit": 10},
                score_listing,
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], "https://www.freelancer.com/projects/website-design/12345")
        self.assertFalse(rows[0]["paid_contract_verified"])
        self.assertEqual(rows[0]["status"], "new_lead")
        self.assertTrue(rows[0]["client_fit"])
        mocked.assert_called_once()
        self.assertIn("limit=10", mocked.call_args.args[0].full_url)

    def test_public_endpoint_rejects_non_freelancer_urls(self):
        payload = {"result": {"projects": [{
            "id": 1, "title": "Website project", "url": "https://example.org/not-freelancer"
        }]}}
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit): return json.dumps(payload).encode()
        with patch("company.freelancer_api_source.urlopen", return_value=Response()):
            self.assertEqual(fetch_public_projects({}, score_listing), [])

    def test_public_endpoint_rejects_oversized_response(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit): return b"x" * (2_000_001)
        with patch("company.freelancer_api_source.urlopen", return_value=Response()):
            with self.assertRaises(ValueError):
                fetch_public_projects({}, score_listing)


if __name__ == "__main__":
    unittest.main()
