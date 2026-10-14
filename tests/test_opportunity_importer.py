import unittest
from company.opportunity_importer import import_report
from company.opportunity_scout import score_listing

class OpportunityImporterTests(unittest.TestCase):
    def test_imports_qualified_listing_as_unverified(self):
        store={"schema_version":1,"leads":[]}
        report={"opportunities":[{"id":"abc","title":"Freelance website redesign","url":"https://example.org/job/1",
            "description":"Paid freelance website redesign; looking for a freelancer to build a website for our small business","source_name":"Example Jobs",
            "score":12,"priority":"high","risk_flags":[],"client_fit":True,"contract_signals":["freelance"],"disqualifiers":[]}]}
        result=import_report(report,store)
        self.assertEqual(result["imported_count"],1)
        lead=store["leads"][0]
        self.assertEqual(lead["source_type"],"public_opportunity_listing")
        self.assertFalse(lead["paid_contract_verified"])
        self.assertFalse(lead["contacted"])
        self.assertIn("verify",lead["next_action"].lower())

    def test_duplicate_source_url_is_not_imported_twice(self):
        store={"schema_version":1,"leads":[]}
        item={"id":"abc","title":"Website design","url":"https://example.org/job/1","description":"Paid freelance website design; looking for a freelancer to build a website for our small business",
              "source_name":"Example","score":8,"priority":"review","risk_flags":[],"client_fit":True,"contract_signals":["contractor"],"disqualifiers":[]}
        report={"opportunities":[item]}
        self.assertEqual(import_report(report,store)["imported_count"],1)
        self.assertEqual(import_report(report,store)["duplicates_skipped"],1)
        self.assertEqual(len(store["leads"]),1)

    def test_imports_freelance_work_without_claiming_it_is_a_client_lead(self):
        store={"schema_version":1,"leads":[]}
        report={"opportunities":[{
            "id":"gig1","title":"Freelance Copywriter",
            "url":"https://example.org/work/freelance-copywriter",
            "description":"Freelance, project-based writing role; paid per article.",
            "source_name":"Example Jobs","score":12,"priority":"high",
            "risk_flags":[],"location_restrictions":[],
            "client_fit":False,"freelance_work_fit":True,
            "opportunity_type":"freelance_work",
            "contract_signals":["freelance"],"project_signals":[],
            "disqualifiers":["no explicit service-project request"]
        }]}
        result=import_report(report,store)
        self.assertEqual(result["imported_count"],1)
        lead=store["leads"][0]
        self.assertFalse(lead["client_fit"])
        self.assertTrue(lead["freelance_work_fit"])
        self.assertEqual(lead["opportunity_type"],"freelance_work")
        self.assertIn("not a direct client lead",lead["next_action"].lower())

    def test_skips_contract_job_without_project_intent(self):
        store={"schema_version":1,"leads":[]}
        report={"opportunities":[{
            "id":"job1","title":"Senior Shopify Developer",
            "url":"https://example.org/job/contract-role",
            "description":"We are hiring a contract-based developer to join our team full-time.",
            "source_name":"Example Jobs","score":14,"priority":"high",
            "risk_flags":[],"client_fit":False,
            "contract_signals":["contract-based"],"project_signals":[],
            "disqualifiers":["no explicit service-project request"]
        }]}
        result=import_report(report,store)
        self.assertEqual(result["imported_count"],0)
        self.assertEqual(result["low_priority_or_risky_skipped"],1)

    def test_skips_listing_with_generic_client_project_wording(self):
        store={"schema_version":1,"leads":[]}
        report={"opportunities":[{
            "id":"job2","title":"Senior Shopify Developer",
            "url":"https://example.org/job/client-project-role",
            "description":"We are hiring a contractor to join our team and support client projects.",
            "source_name":"Example Jobs","score":14,"priority":"high",
            "risk_flags":[],"client_fit":False,
            "contract_signals":["contractor"],"project_signals":[],
            "disqualifiers":["no explicit service-project request"]
        }]}
        result=import_report(report,store)
        self.assertEqual(result["imported_count"],0)

    def test_skips_risky_and_low_priority(self):
        store={"schema_version":1,"leads":[]}
        report={"opportunities":[
          {"title":"Pay to apply website role","url":"https://example.org/1","description":"pay to apply",
           "source_name":"Example","score":10,"priority":"low","risk_flags":["pay to apply"],"client_fit":False,"disqualifiers":["pay to apply"]},
          {"title":"Weak listing","url":"https://example.org/2","description":"misc",
           "source_name":"Example","score":1,"priority":"low","risk_flags":[],"client_fit":False,"disqualifiers":["no contract signal"]}
        ]}
        result=import_report(report,store)
        self.assertEqual(result["imported_count"],0)
        self.assertEqual(result["low_priority_or_risky_skipped"],2)

    def test_non_https_or_missing_url_skipped(self):
        store={"schema_version":1,"leads":[]}
        report={"opportunities":[{"title":"bad link","url":"http://example.org","priority":"high","score":20,"client_fit":True,"contract_signals":["freelance"],"disqualifiers":[]}]}
        self.assertEqual(import_report(report,store)["imported_count"],0)

    def test_ordinary_employment_is_not_client_fit(self):
        result = score_listing(
            "Head of Marketing",
            "Full-time remote role with salary and benefits; lead the marketing team."
        )
        self.assertFalse(result["client_fit"])
        self.assertEqual(result["priority"], "low")

    def test_explicit_remote_freelance_project_can_qualify(self):
        result = score_listing(
            "Freelance Shopify Website Project",
            "Remote paid project for a small business; looking for a freelancer to build a Shopify website; fixed-price contract."
        )
        self.assertTrue(result["client_fit"])
        self.assertIn("freelance", result["contract_signals"])
        self.assertIn(result["priority"], {"high", "review"})

    def test_onsite_contract_is_excluded(self):
        result = score_listing(
            "Contract Website Designer (Onsite)",
            "Six-month contractor engagement, onsite in Lisbon."
        )
        self.assertFalse(result["client_fit"])
        self.assertTrue(result["location_restrictions"])

if __name__ == "__main__": unittest.main()
