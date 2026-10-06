import unittest
from unittest.mock import patch
import uuid
import random

from skills.market_portfolio_audit_integrity_reporter import (
    MarketPortfolioAuditIntegrityReporter,
    market_portfolio_audit_integrity_reporter
)

class TestMarketPortfolioAuditIntegrityReporter(unittest.TestCase):

    def test_reporter_class_success_passed(self):
        audit_id = uuid.uuid4().hex
        mock_db = unittest.mock.MagicMock()
        mock_db.get_audit_record.return_value = {"discrepancies": []}

        reporter = MarketPortfolioAuditIntegrityReporter(db_storage=mock_db)
        report = reporter.generate_audit_report(audit_id)

        self.assertEqual(report["audit_id"], audit_id)
        self.assertEqual(report["status"], "PASSED")
        self.assertEqual(report["discrepancies_count"], 0)
        self.assertEqual(report["details"], [])
        mock_db.save_integrity_report.assert_called_once_with(audit_id, report)

    def test_reporter_class_success_failed(self):
        audit_id = uuid.uuid4().hex
        disc_item = uuid.uuid4().hex
        mock_db = unittest.mock.MagicMock()
        mock_db.get_audit_record.return_value = {"discrepancies": [disc_item]}

        reporter = MarketPortfolioAuditIntegrityReporter(db_storage=mock_db)
        report = reporter.generate_audit_report(audit_id)

        self.assertEqual(report["audit_id"], audit_id)
        self.assertEqual(report["status"], "FAILED")
        self.assertEqual(report["discrepancies_count"], 1)
        self.assertIn(disc_item, report["details"])
        mock_db.save_integrity_report.assert_called_once_with(audit_id, report)

    def test_reporter_class_empty_audit_id_raises_value_error(self):
        mock_db = unittest.mock.MagicMock()
        reporter = MarketPortfolioAuditIntegrityReporter(db_storage=mock_db)
        with self.assertRaises(ValueError):
            reporter.generate_audit_report("")

    def test_reporter_class_not_found_raises_lookup_error(self):
        audit_id = uuid.uuid4().hex
        mock_db = unittest.mock.MagicMock()
        mock_db.get_audit_record.return_value = None

        reporter = MarketPortfolioAuditIntegrityReporter(db_storage=mock_db)
        with self.assertRaises(LookupError):
            reporter.generate_audit_report(audit_id)

    @patch("skills.market_portfolio_audit_integrity_reporter.db_storage")
    def test_functional_reporter_passed(self, mock_db_storage):
        portfolio_id = uuid.uuid4().hex
        audit_session_id = uuid.uuid4().hex
        key_k = uuid.uuid4().hex
        val_v = uuid.uuid4().hex

        reporter_input = {
            "portfolio_id": portfolio_id,
            "audit_session_id": audit_session_id,
            "report_data": {key_k: val_v},
            "discrepancy_detected": False
        }

        output = market_portfolio_audit_integrity_reporter(reporter_input)

        self.assertEqual(output["portfolio_id"], portfolio_id)
        self.assertEqual(output["audit_session_id"], audit_session_id)
        self.assertEqual(output["status"], "PASSED")
        self.assertEqual(output["discrepancy"], 0.0)
        self.assertEqual(output["report_data"][key_k], val_v)
        mock_db_storage.assert_called_once()

    @patch("skills.market_portfolio_audit_integrity_reporter.db_storage")
    def test_functional_reporter_failed(self, mock_db_storage):
        portfolio_id = uuid.uuid4().hex
        audit_session_id = uuid.uuid4().hex
        disc_val = round(random.uniform(1.0, 1000.0), 2)

        reporter_input = {
            "portfolio_id": portfolio_id,
            "audit_session_id": audit_session_id,
            "report_data": {"discrepancy": disc_val},
            "discrepancy_detected": True
        }

        output = market_portfolio_audit_integrity_reporter(reporter_input)

        self.assertEqual(output["portfolio_id"], portfolio_id)
        self.assertEqual(output["audit_session_id"], audit_session_id)
        self.assertEqual(output["status"], "FAILED")
        self.assertEqual(output["discrepancy"], disc_val)
        mock_db_storage.assert_called_once()

if __name__ == "__main__":
    unittest.main()