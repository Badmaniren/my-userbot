import unittest
import os
import uuid
import tempfile
from skills.market_portfolio_stress_audit_summary_ledger import (
    MarketPortfolioStressAuditSummaryLedger,
    market_portfolio_stress_audit_summary_ledger
)
from skills.db_storage import db_storage

class RealDatabaseStub:
    def __init__(self):
        self.store = {}

    def save(self, key, value):
        self.store[key] = value

    def save_summary(self, audit_payload: dict) -> bool:
        key = audit_payload.get("audit_id", str(uuid.uuid4()))
        self.store[key] = audit_payload
        return True

    def get_by_id(self, ledger_id: str) -> dict:
        return self.store.get(ledger_id)

    def get_export_stream(self):
        import io
        return io.BytesIO(b"exported_ledger_data")

class TestMarketPortfolioStressAuditSummaryLedgerIntegration(unittest.TestCase):
    def setUp(self):
        self.db = RealDatabaseStub()
        self.ledger_service = MarketPortfolioStressAuditSummaryLedger(self.db)
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_end_to_end_audit_ledger_workflow(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        audit_id = f"audit-{uuid.uuid4()}"
        stress_score = round(float(uuid.uuid4().int % 100) + 5.5, 2)
        ledger_path = os.path.join(self.test_dir.name, f"ledger_{uuid.uuid4()}.txt")

        initial_data = {
            "portfolio_id": portfolio_id,
            "audit_id": audit_id,
            "stress_score": stress_score,
            "ledger_path": ledger_path
        }

        result = market_portfolio_stress_audit_summary_ledger(initial_data, self.db)

        self.assertEqual(result["audit_id"], audit_id)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["stress_score"], stress_score)

        self.assertTrue(os.path.exists(ledger_path))
        with open(ledger_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(audit_id, content)
            self.assertIn(portfolio_id, content)
            self.assertIn(str(stress_score), content)

        payload = {
            "audit_id": audit_id,
            "portfolio_id": portfolio_id,
            "stress_score": stress_score,
            "status": "VERIFIED"
        }
        save_success = self.ledger_service.record_audit_summary(payload)
        self.assertTrue(save_success)

        fetched_record = self.ledger_service.fetch_audit_summary(audit_id)
        self.assertEqual(fetched_record["audit_id"], audit_id)
        self.assertEqual(fetched_record["status"], "VERIFIED")

        export_stream = self.ledger_service.export_audit_ledger()
        self.assertIsNotNone(export_stream)
        self.assertEqual(export_stream.getvalue(), b"exported_ledger_data")

    def test_invalid_data_raises_error(self):
        invalid_data = {
            "portfolio_id": "",
            "audit_id": None,
            "stress_score": "not_a_number",
            "ledger_path": ""
        }
        with self.assertRaises(ValueError):
            market_portfolio_stress_audit_summary_ledger(invalid_data, self.db)

    def test_fetch_nonexistent_ledger_raises_error(self):
        fake_id = f"missing-{uuid.uuid4()}"
        with self.assertRaises(ValueError):
            self.ledger_service.fetch_audit_summary(fake_id)

if __name__ == "__main__":
    unittest.main()