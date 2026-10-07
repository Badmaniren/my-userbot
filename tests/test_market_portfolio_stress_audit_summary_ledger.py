import unittest
from unittest.mock import MagicMock, patch, mock_open
import io
import uuid
import random
import os
from skills.market_portfolio_stress_audit_summary_ledger import (
    MarketPortfolioStressAuditSummaryLedger,
    market_portfolio_stress_audit_summary_ledger
)

class TestMarketPortfolioStressAuditSummaryLedger(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.ledger = MarketPortfolioStressAuditSummaryLedger(self.mock_db)

    def test_record_audit_summary_success(self):
        payload = {
            str(uuid.uuid4()): str(uuid.uuid4()),
            "score": random.uniform(1.0, 100.0)
        }
        self.mock_db.save_summary.return_value = True
        result = self.ledger.record_audit_summary(payload)
        self.assertTrue(result)
        self.mock_db.save_summary.assert_called_once_with(payload)

    def test_fetch_audit_summary_success(self):
        ledger_id = uuid.uuid4().hex
        expected_record = {
            "ledger_id": ledger_id,
            "data": uuid.uuid4().hex
        }
        self.mock_db.get_by_id.return_value = expected_record
        result = self.ledger.fetch_audit_summary(ledger_id)
        self.assertEqual(result, expected_record)
        self.mock_db.get_by_id.assert_called_once_with(ledger_id)

    def test_fetch_audit_summary_not_found(self):
        ledger_id = uuid.uuid4().hex
        self.mock_db.get_by_id.return_value = None
        with self.assertRaises(ValueError) as ctx:
            self.ledger.fetch_audit_summary(ledger_id)
        self.assertIn(ledger_id, str(ctx.exception))

    def test_export_audit_ledger(self):
        mock_stream = io.BytesIO(uuid.uuid4().bytes)
        self.mock_db.get_export_stream.return_value = mock_stream
        result = self.ledger.export_audit_ledger()
        self.assertEqual(result, mock_stream)
        self.mock_db.get_export_stream.assert_called_once()

    def test_functional_helper_success(self):
        portfolio_id = uuid.uuid4().hex
        audit_id = uuid.uuid4().hex
        stress_score = round(random.uniform(0.0, 100.0), 2)
        ledger_path = f"/tmp/{uuid.uuid4().hex}.log"

        initial_data = {
            "portfolio_id": portfolio_id,
            "audit_id": audit_id,
            "stress_score": stress_score,
            "ledger_path": ledger_path
        }

        mock_db_func = MagicMock()

        with patch("builtins.open", mock_open()) as mock_file:
            res = market_portfolio_stress_audit_summary_ledger(initial_data, mock_db_func)

            self.assertEqual(res["portfolio_id"], portfolio_id)
            self.assertEqual(res["audit_id"], audit_id)
            self.assertEqual(res["stress_score"], stress_score)

            mock_db_func.save.assert_called_once_with(audit_id, res)
            mock_file.assert_called_once_with(ledger_path, "w", encoding="utf-8")

            handle = mock_file()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)
            self.assertIn(audit_id, written_content)
            self.assertIn(portfolio_id, written_content)
            self.assertIn(str(stress_score), written_content)

    def test_functional_helper_invalid_data(self):
        invalid_cases = [
            {},
            {"portfolio_id": uuid.uuid4().hex},
            {"portfolio_id": uuid.uuid4().hex, "audit_id": uuid.uuid4().hex},
            {"portfolio_id": uuid.uuid4().hex, "audit_id": uuid.uuid4().hex, "stress_score": "not_a_number", "ledger_path": "/tmp/a.log"},
            {"portfolio_id": uuid.uuid4().hex, "audit_id": uuid.uuid4().hex, "stress_score": 10.5, "ledger_path": ""}
        ]

        mock_db_func = MagicMock()
        for data in invalid_cases:
            with self.assertRaises(ValueError):
                market_portfolio_stress_audit_summary_ledger(data, mock_db_func)

if __name__ == "__main__":
    unittest.main()
