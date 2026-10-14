import unittest
from company.opportunity_importer import import_report

class OpportunityImporterTests(unittest.TestCase):
    def test_imports_qualified_listing_as_unverified(self):
        store={"schema_version":1,"leads":[]}
        report={"opportunities":[{"id":"abc","title":"Freelance website redesign","url":"https://example.org/job/1",
            "description":"Paid freelance website redesign for a small business","source_name":"Example Jobs",
            "score":12,"priority":"high","risk_flags":[]}]}
        result=import_report(report,store)
        self.assertEqual(result["imported_count"],1)
        lead=store["leads"][0]
        self.assertEqual(lead["source_type"],"public_opportunity_listing")
        self.assertFalse(lead["paid_contract_verified"])
        self.assertFalse(lead["contacted"])
        self.assertIn("verify",lead["next_action"].lower())

    def test_duplicate_source_url_is_not_imported_twice(self):
        store={"schema_version":1,"leads":[]}
        item={"id":"abc","title":"Website design","url":"https://example.org/job/1","description":"Paid web design",
              "source_name":"Example","score":8,"priority":"review","risk_flags":[]}
        report={"opportunities":[item]}
        self.assertEqual(import_report(report,store)["imported_count"],1)
        self.assertEqual(import_report(report,store)["duplicates_skipped"],1)
        self.assertEqual(len(store["leads"]),1)

    def test_skips_risky_and_low_priority(self):
        store={"schema_version":1,"leads":[]}
        report={"opportunities":[
          {"title":"Pay to apply website role","url":"https://example.org/1","description":"pay to apply",
           "source_name":"Example","score":10,"priority":"review","risk_flags":["pay to apply"]},
          {"title":"Weak listing","url":"https://example.org/2","description":"misc",
           "source_name":"Example","score":1,"priority":"low","risk_flags":[]}
        ]}
        result=import_report(report,store)
        self.assertEqual(result["imported_count"],0)
        self.assertEqual(result["low_priority_or_risky_skipped"],2)

    def test_non_https_or_missing_url_skipped(self):
        store={"schema_version":1,"leads":[]}
        report={"opportunities":[{"title":"bad link","url":"http://example.org","priority":"high","score":20}]}
        self.assertEqual(import_report(report,store)["imported_count"],0)

if __name__ == "__main__": unittest.main()
