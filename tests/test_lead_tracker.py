import tempfile, unittest
from pathlib import Path
from company.lead_tracker import add_lead, update_lead, summary, load_store, save_store

class LeadTrackerTests(unittest.TestCase):
    def test_add_update_persist_and_summary(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"leads.json"
            store=load_store(path)
            lead=add_lead(store,business_name="Cafe",service="website",need="Needs menu page",evidence="Human checked")
            save_store(store,path)
            loaded=load_store(path)
            update_lead(loaded,lead["id"],status="paid_verified",revenue_inr=2500,revenue_evidence="Operator verified receipt")
            save_store(loaded,path)
            result=summary(load_store(path))
            self.assertEqual(result["total_leads"],1)
            self.assertEqual(result["verified_revenue_inr"],2500)
    def test_revenue_requires_verified_status_and_evidence(self):
        store={"leads":[]}
        lead=add_lead(store,business_name="Cafe",service="website",need="Needs a site")
        with self.assertRaises(ValueError):
            update_lead(store,lead["id"],revenue_inr=100,revenue_evidence="receipt")
        with self.assertRaises(ValueError):
            update_lead(store,lead["id"],status="paid_verified",revenue_inr=100)
    def test_do_not_contact_guard(self):
        store={"leads":[]}
        lead=add_lead(store,business_name="Cafe",service="website",need="Needs a site")
        update_lead(store,lead["id"],status="do_not_contact")
        with self.assertRaises(ValueError):
            update_lead(store,lead["id"],contacted=True)
    def test_invalid_status_rejected(self):
        store={"leads":[]}
        lead=add_lead(store,business_name="Cafe",service="website",need="Needs a site")
        with self.assertRaises(ValueError):
            update_lead(store,lead["id"],status="maybe")

if __name__ == "__main__": unittest.main()
