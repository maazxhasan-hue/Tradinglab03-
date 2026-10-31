import hashlib, hmac, json, tempfile, time, unittest
from pathlib import Path
from company.revenue_ledger import RevenueLedger, verify_stripe_signature

def signed(payload, secret, timestamp):
    digest=hmac.new(secret.encode(),str(timestamp).encode()+b"."+payload,hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"

class RevenueLedgerTests(unittest.TestCase):
    def test_signature_verification_and_expiry(self):
        payload=b'{"id":"evt_1"}'
        header=signed(payload,"whsec_test",1000)
        self.assertTrue(verify_stripe_signature(payload,header,"whsec_test",now=1000))
        self.assertFalse(verify_stripe_signature(payload,header,"wrong",now=1000))
        self.assertFalse(verify_stripe_signature(payload,header,"whsec_test",now=2000))
    def test_paid_event_is_idempotent(self):
        secret="whsec_test"; now=int(time.time())
        payload=json.dumps({"id":"evt_paid_1","type":"checkout.session.completed","data":{"object":{"id":"cs_1","payment_status":"paid","amount_total":99900,"currency":"inr"}}}).encode()
        header=signed(payload,secret,now)
        with tempfile.TemporaryDirectory() as td:
            ledger=RevenueLedger(Path(td)/"revenue.sqlite3")
            first=ledger.ingest_stripe_event(payload,header,secret,now=now)
            second=ledger.ingest_stripe_event(payload,header,secret,now=now)
            self.assertEqual(first["status"],"paid")
            self.assertFalse(first["duplicate"])
            self.assertTrue(second["duplicate"])
            self.assertEqual(ledger.summary()["provider_events"][0]["amount_minor"],99900)
    def test_unpaid_checkout_is_not_revenue(self):
        secret="whsec_test"; now=int(time.time())
        payload=json.dumps({"id":"evt_unpaid","type":"checkout.session.completed","data":{"object":{"id":"cs_2","payment_status":"unpaid","amount_total":99900,"currency":"inr"}}}).encode()
        with tempfile.TemporaryDirectory() as td:
            ledger=RevenueLedger(Path(td)/"revenue.sqlite3")
            result=ledger.ingest_stripe_event(payload,signed(payload,secret,now),secret,now=now)
            self.assertEqual(result["status"],"ignored")
            self.assertEqual(result["amount_minor"],0)
    def test_invalid_signature_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ledger=RevenueLedger(Path(td)/"revenue.sqlite3")
            with self.assertRaises(ValueError):
                ledger.ingest_stripe_event(b'{}',"t=1,v1=bad","whsec_test",now=1)

if __name__ == "__main__": unittest.main()
