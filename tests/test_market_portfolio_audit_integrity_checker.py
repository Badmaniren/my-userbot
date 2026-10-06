import unittest
from unittest.mock import patch
import io
import uuid
import random
import string
from skills.market_portfolio_audit_integrity_checker import (
    MarketPortfolioAuditIntegrityChecker,
    market_portfolio_audit_log_exporter,
    market_portfolio_collector_agent,
    market_portfolio_audit_integrity_checker
)


class TestMarketPortfolioAuditIntegrityChecker(unittest.TestCase):

    def setUp(self):
        self.random_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.random_audit_file = f"audit_{uuid.uuid4().hex[:8]}.log"
        self.random_tx_id = f"tx_{uuid.uuid4().hex[:8]}"
        self.random_amount = round(random.uniform(10.0, 9999.9), 2)
        self.random_stream_data = "".join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')

    def test_init_and_attributes(self):
        dummy_storage = "dummy_db_reference"
        checker = MarketPortfolioAuditIntegrityChecker(db_storage=dummy_storage, custom_param=self.random_portfolio_id)
        self.assertEqual(checker.db_storage, dummy_storage)
        self.assertEqual(checker.custom_param, self.random_portfolio_id)

    def test_run_audit_integrity_check_no_storage(self):
        checker = MarketPortfolioAuditIntegrityChecker()
        res = checker.run_audit_integrity_check()
        self.assertFalse(res["anomalies_detected"])
        self.assertEqual(res["discrepancies"], [])

    def test_run_audit_integrity_check_with_discrepancies(self):
        mock_storage = unittest.mock.MagicMock()
        tx_id_1 = f"tx_{uuid.uuid4().hex[:6]}"
        tx_id_2 = f"tx_{uuid.uuid4().hex[:6]}"

        amount_1 = round(random.uniform(100.0, 500.0), 2)
        amount_2 = round(random.uniform(600.0, 1000.0), 2)
        audit_amount_1 = amount_1
        audit_amount_2 = amount_2 + 50.0

        mock_storage.get_transactions.return_value = [
            {"id": tx_id_1, "amount": amount_1},
            {"id": tx_id_2, "amount": amount_2}
        ]
        mock_storage.get_audit_logs.return_value = [
            {"tx_id": tx_id_1, "amount": audit_amount_1},
            {"tx_id": tx_id_2, "amount": audit_amount_2}
        ]

        checker = MarketPortfolioAuditIntegrityChecker(db_storage=mock_storage)
        res = checker.run_audit_integrity_check()

        self.assertTrue(res["anomalies_detected"])
        self.assertEqual(len(res["discrepancies"]), 1)
        self.assertEqual(res["discrepancies"][0]["tx_id"], tx_id_2)
        self.assertEqual(res["discrepancies"][0]["transaction_amount"], amount_2)
        self.assertEqual(res["discrepancies"][0]["audit_amount"], audit_amount_2)

    def test_run_audit_integrity_check_missing_in_audit(self):
        mock_storage = unittest.mock.MagicMock()
        tx_id = f"tx_{uuid.uuid4().hex[:6]}"
        amount = round(random.uniform(10.0, 50.0), 2)

        mock_storage.get_transactions.return_value = [{"id": tx_id, "amount": amount}]
        mock_storage.get_audit_logs.return_value = []

        checker = MarketPortfolioAuditIntegrityChecker(db_storage=mock_storage)
        res = checker.run_audit_integrity_check()

        self.assertTrue(res["anomalies_detected"])
        self.assertEqual(len(res["discrepancies"]), 1)
        self.assertEqual(res["discrepancies"][0]["tx_id"], tx_id)
        self.assertEqual(res["discrepancies"][0]["transaction_amount"], amount)
        self.assertIsNone(res["discrepancies"][0]["audit_amount"])

    def test_parse_external_audit_stream(self):
        checker = MarketPortfolioAuditIntegrityChecker()
        stream = io.BytesIO(self.random_stream_data)
        parsed_res = checker.parse_external_audit_stream(stream)

        self.assertTrue(parsed_res["parsed"])
        self.assertEqual(parsed_res["size"], len(self.random_stream_data))

    def test_market_portfolio_audit_integrity_checker_entrypoint(self):
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "audit_file": self.random_audit_file
        }
        response = market_portfolio_audit_integrity_checker(payload)

        self.assertEqual(response["status"], "SUCCESS")
        self.assertEqual(response["checked_portfolio"], self.random_portfolio_id)
        self.assertEqual(response["audit_file"], self.random_audit_file)


if __name__ == '__main__':
    unittest.main()