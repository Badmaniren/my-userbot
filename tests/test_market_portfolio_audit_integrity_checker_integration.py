import unittest
import uuid
import random
from skills.db_storage import db_storage
from skills.market_portfolio_audit_integrity_checker import (
    MarketPortfolioAuditIntegrityChecker,
    market_portfolio_audit_integrity_checker
)


class TestMarketPortfolioAuditIntegrityCheckerIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.tx_id_1 = str(uuid.uuid4())
        self.tx_id_2 = str(uuid.uuid4())

        self.amount_match = round(random.uniform(100.0, 1000.0), 2)
        self.amount_mismatch_tx = round(random.uniform(1000.1, 5000.0), 2)
        self.amount_mismatch_audit = round(random.uniform(5001.0, 10000.0), 2)

        self.test_transactions = [
            {"id": self.tx_id_1, "amount": self.amount_match},
            {"id": self.tx_id_2, "amount": self.amount_mismatch_tx}
        ]

        self.test_audit_logs = [
            {"tx_id": self.tx_id_1, "amount": self.amount_match},
            {"tx_id": self.tx_id_2, "amount": self.amount_mismatch_audit}
        ]

    def test_audit_integrity_check_with_real_db_storage(self):
        class RealDBStorageStub:
            def __init__(self, txs, logs):
                self.txs = txs
                self.logs = logs

            def get_transactions(self):
                return self.txs

            def get_audit_logs(self):
                return self.logs

        db_stub = RealDBStorageStub(self.test_transactions, self.test_audit_logs)
        checker = MarketPortfolioAuditIntegrityChecker(db_storage=db_stub)

        result = checker.run_audit_integrity_check()

        self.assertIn("anomalies_detected", result)
        self.assertIn("discrepancies", result)
        self.assertTrue(result["anomalies_detected"])

        discrepancies = result["discrepancies"]
        self.assertEqual(len(discrepancies), 1)

        disc = discrepancies[0]
        self.assertEqual(disc["tx_id"], self.tx_id_2)
        self.assertEqual(disc["transaction_amount"], self.amount_mismatch_tx)
        self.assertEqual(disc["audit_amount"], self.amount_mismatch_audit)

    def test_market_portfolio_audit_integrity_checker_payload(self):
        audit_file_name = f"audit_{uuid.uuid4()}.log"
        payload = {
            "portfolio_id": self.portfolio_id,
            "audit_file": audit_file_name
        }

        response = market_portfolio_audit_integrity_checker(payload)

        self.assertIsInstance(response, dict)
        self.assertEqual(response.get("status"), "SUCCESS")
        self.assertEqual(response.get("checked_portfolio"), self.portfolio_id)
        self.assertEqual(response.get("audit_file"), audit_file_name)


if __name__ == "__main__":
        unittest.main()