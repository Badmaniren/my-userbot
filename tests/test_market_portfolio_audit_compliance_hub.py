import unittest
from unittest.mock import MagicMock, patch
import os
import uuid
import random
import io
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub

class TestMarketPortfolioAuditComplianceHub(unittest.TestCase):

    def setUp(self) -> None:
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.mock_db = MagicMock()
        self.mock_exporter = MagicMock()
        self.hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.random_storage,
            db_storage=self.mock_db,
            audit_exporter=self.mock_exporter
        )

    def tearDown(self) -> None:
        if os.path.exists(self.random_storage):
            try:
                os.remove(self.random_storage)
            except OSError:
                pass

    def test_run_compliance_export_success(self) -> None:
        export_path = f"{uuid.uuid4().hex}.json"
        self.mock_exporter.export_audit_logs.return_value = True

        res = self.hub.run_compliance_export(export_path)

        self.assertTrue(res)
        self.mock_exporter.export_audit_logs.assert_called_once_with(export_path)
        if os.path.exists(export_path):
            os.remove(export_path)

    def test_run_compliance_export_fallback_creation(self) -> None:
        export_path = f"{uuid.uuid4().hex}.json"
        self.mock_exporter.export_audit_logs.return_value = False

        res = self.hub.run_compliance_export(export_path)

        self.assertTrue(res)
        self.assertTrue(os.path.exists(export_path))
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "{}")
        os.remove(export_path)

    def test_check_compliance_integrity_true(self) -> None:
        self.mock_exporter.verify_log_integrity.return_value = True
        res = self.hub.check_compliance_integrity()
        self.assertTrue(res)

    def test_check_compliance_integrity_fallback(self) -> None:
        self.mock_exporter.verify_log_integrity.return_value = False
        res = self.hub.check_compliance_integrity()
        self.assertTrue(res)

    def test_fetch_compliance_summary_data(self) -> None:
        expected_summary = {uuid.uuid4().hex: random.randint(1, 100)}
        self.mock_exporter.get_audit_stream_summary.return_value = expected_summary

        res = self.hub.fetch_compliance_summary()
        self.assertEqual(res, expected_summary)

    def test_fetch_compliance_summary_empty(self) -> None:
        self.mock_exporter.get_audit_stream_summary.return_value = None
        res = self.hub.fetch_compliance_summary()
        self.assertEqual(res, {})

    def test_process_audit_stream_data(self) -> None:
        export_path = f"{uuid.uuid4().hex}.log"
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        self.mock_exporter.process_audit_stream.return_value = True

        res = self.hub.process_audit_stream_data(export_path, stream_data)
        self.assertTrue(res)
        self.mock_exporter.process_audit_stream.assert_called_once_with(export_path, stream_data)

    def test_generate_compliance_log(self) -> None:
        export_path = f"{uuid.uuid4().hex}.log"
        self.mock_exporter.generate_audit_log.return_value = True

        res = self.hub.generate_compliance_log(export_path)
        self.assertTrue(res)
        self.mock_exporter.generate_audit_log.assert_called_once_with(export_path)

    def test_audit_fetch_market_price_valid(self) -> None:
        url = f"https://{uuid.uuid4().hex}.market/api"
        expected_price = round(random.uniform(10.0, 1000.0), 2)
        self.mock_db.fetch_price.return_value = expected_price

        res = self.hub.audit_fetch_market_price(url)
        self.assertEqual(res, float(expected_price))
        self.mock_db.fetch_price.assert_called_once_with(url)

    def test_audit_fetch_market_price_exception(self) -> None:
        url = f"https://{uuid.uuid4().hex}.market/api"
        self.mock_db.fetch_price.side_effect = ConnectionError(uuid.uuid4().hex)

        res = self.hub.audit_fetch_market_price(url)
        self.assertEqual(res, 0.0)

    def test_load_historical_audit_data_exists(self) -> None:
        filename = f"{uuid.uuid4().hex}.json"
        expected_data = [{uuid.uuid4().hex: uuid.uuid4().hex}]
        self.mock_db.load_data.return_value = expected_data

        with open(filename, "w", encoding="utf-8") as f:
            f.write("[]")

        res = self.hub.load_historical_audit_data(filename)
        self.assertEqual(res, expected_data)
        os.remove(filename)

    def test_load_historical_audit_data_missing(self) -> None:
        filename = f"{uuid.uuid4().hex}.json"
        self.assertFalse(os.path.exists(filename))
        self.mock_db.load_data.return_value = None

        res = self.hub.load_historical_audit_data(filename)
        self.assertEqual(res, [])
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)

    def test_get_audit_stream_summary(self) -> None:
        summary_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_exporter.get_audit_stream_summary.return_value = summary_data

        res = self.hub.get_audit_stream_summary()
        self.assertEqual(res, summary_data)

    def test_verify_log_integrity(self) -> None:
        self.mock_exporter.verify_log_integrity.return_value = False
        res = self.hub.verify_log_integrity()
        self.assertTrue(res)

    def test_export_audit_logs(self) -> None:
        export_path = f"{uuid.uuid4().hex}.json"
        self.mock_exporter.export_audit_logs.return_value = None

        res = self.hub.export_audit_logs(export_path)
        self.assertTrue(res)
        self.assertTrue(os.path.exists(export_path))
        os.remove(export_path)

if __name__ == "__main__":
    unittest.main()