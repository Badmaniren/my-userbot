import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_audit_reconciliation_engine import market_portfolio_audit_reconciliation_engine
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_audit_log_exporter import market_portfolio_audit_log_exporter

class TestMarketPortfolioAuditReconciliationEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.test_dir.name, f"test_audit_{uuid.uuid4()}.db")
        self.portfolio_id = str(uuid.uuid4())
        self.asset_ticker = f"ASSET_{random.randint(1000, 9999)}"
        self.quantity = round(random.uniform(10.0, 1000.0), 4)
        self.price = round(random.uniform(50.0, 500.0), 2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_reconciliation_engine_real_integration(self):
        db_instance = db_storage()

        collector_input = {
            "portfolio_id": self.portfolio_id,
            "ticker": self.asset_ticker,
            "quantity": self.quantity,
            "price": self.price,
            "timestamp": random.randint(1600000000, 1700000000)
        }

        collector_result = market_portfolio_collector_agent(collector_input)
        self.assertIsNotNone(collector_result)

        audit_log_data = {
            "event_id": str(uuid.uuid4()),
            "portfolio_id": self.portfolio_id,
            "action": "SNAPSHOT_RECORDED",
            "details": collector_result
        }

        export_result = market_portfolio_audit_log_exporter(audit_log_data)
        self.assertIsNotNone(export_result)

        engine_payload = {
            "db_path": self.db_path,
            "portfolio_id": self.portfolio_id,
            "reconciliation_mode": "strict",
            "tolerance": 0.001
        }

        reconciliation_output = market_portfolio_audit_reconciliation_engine(engine_payload)

        self.assertIsInstance(reconciliation_output, dict)
        self.assertIn("discrepancies_found", reconciliation_output)
        self.assertIn("audit_status", reconciliation_output)
        self.assertEqual(reconciliation_output.get("portfolio_id"), self.portfolio_id)

if __name__ == "__main__":
    unittest.main()