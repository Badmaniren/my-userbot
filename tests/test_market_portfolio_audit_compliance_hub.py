import unittest
from unittest.mock import MagicMock, patch
import os
import uuid
import random
import string
import io
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub


class TestMarketPortfolioAuditComplianceHub(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.mock_db = MagicMock()
        self.mock_exporter = MagicMock()

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_init_default_and_custom(self):
        hub_custom = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.mock_db,
            audit_exporter=self.mock_exporter
        )
        self.assertEqual(hub_custom.db_storage, self.mock_db)
        self.assertEqual(hub_custom.audit_exporter, self.mock_exporter)

        hub_default = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)
        self.assertIsNotNone(hub_default.db_storage)
        self.assertIsNotNone(hub_default.audit_exporter)

    def test_run_compliance_export_success(self):
        export_path = f"{uuid.uuid4().hex}.log"
        expected_result = random.choice([True, {"status": uuid.uuid4().hex}])
        self.mock_exporter.export_audit_logs.return_value = expected_result

        hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            audit_exporter=self.mock_exporter
        )
        res = hub.run_compliance_export(export_path)
        self.assertEqual(res, expected_result)
        self.mock_exporter.export_audit_logs.assert_called_once_with(export_path)

    def test_run_compliance_export_fallback_creates_file(self):
        export_path = f"{uuid.uuid4().hex}_missing.json"
        self.mock_exporter.export_audit_logs.return_value = False

        hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            audit_exporter=self.mock_exporter
        )

        self.assertFalse(os.path.exists(export_path))
        res = hub.run_compliance_export(export_path)

        self.assertTrue(res)
        self.assertTrue(os.path.exists(export_path))
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertEqual(content, "{}")

        if os.path.exists(export_path):
            os.remove(export_path)

    def test_check_compliance_integrity_none_returns_true(self):
        self.mock_exporter.verify_log_integrity.return_value = None

        hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            audit_exporter=self.mock_exporter
        )
        res = hub.check_compliance_integrity()
        self.assertTrue(res)

    def test_check_compliance_integrity_explicit_value(self):
        expected = random.choice([True, False])
        self.mock_exporter.verify_log_integrity.return_value = expected

        hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            audit_exporter=self.mock_exporter
        )
        res = hub.check_compliance_integrity()
        self.assertEqual(res, expected)

    def test_fetch_compliance_summary(self):
        summary_data = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}
        self.mock_exporter.get_audit_stream_summary.return_value = summary_data

        hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            audit_exporter=self.mock_exporter
        )
        res = hub.fetch_compliance_summary()
        self.assertEqual(res, summary_data)

    def test_process_audit_stream_data(self):
        export_path = f"{uuid.uuid4().hex}.stream"
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        self.mock_exporter.process_audit_stream.return_value = None

        hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            audit_exporter=self.mock_exporter
        )
        res = hub.process_audit_stream_data(export_path, stream_data)
        self.assertTrue(res)
        self.mock_exporter.process_audit_stream.assert_called_once_with(export_path, stream_data)

    def test_generate_compliance_log(self):
        export_path = f"{uuid.uuid4().hex}.log"
        self.mock_exporter.generate_audit_log.return_value = None

        hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            audit_exporter=self.mock_exporter
        )
        res = hub.generate_compliance_log(export_path)
        self.assertTrue(res)
        self.mock_exporter.generate_audit_log.assert_called_once_with(export_path)

    def test_audit_fetch_market_price(self):
        url = f"https://{uuid.uuid4().hex}.market/api/v1/price"
        expected_price = round(random.uniform(10.0, 1000.0), 2)
        self.mock_db.fetch_price.return_value = expected_price

        hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.mock_db
        )
        res = hub.audit_fetch_market_price(url)
        self.assertEqual(res, expected_price)
        self.mock_db.fetch_price.assert_called_once_with(url)

    def test_load_historical_audit_data(self):
        filename = f"{uuid.uuid4().hex}_history.dat"
        historical_payload = [uuid.uuid4().hex, random.randint(1, 100)]
        self.mock_db.load_data.return_value = historical_payload

        hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.mock_db
        )
        res = hub.load_historical_audit_data(filename)
        self.assertEqual(res, historical_payload)
        self.mock_db.load_data.assert_called_once_with(filename)

    def test_get_audit_stream_summary_delegation(self):
        summary_payload = {uuid.uuid4().hex: random.random()}
        self.mock_exporter.get_audit_stream_summary.return_value = summary_payload

        hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            audit_exporter=self.mock_exporter
        )
        res = hub.get_audit_stream_summary()
        self.assertEqual(res, summary_payload)

    def test_verify_log_integrity(self):
        self.mock_exporter.verify_log_integrity.return_value = None

        hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            audit_exporter=self.mock_exporter
        )
        res = hub.verify_log_integrity()
        self.assertTrue(res)

    def test_export_audit_logs_passthrough(self):
        export_path = f"{uuid.uuid4().hex}.export"
        custom_response = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_exporter.export_audit_logs.return_value = custom_response

        hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            audit_exporter=self.mock_exporter
        )
        res = hub.export_audit_logs(export_path)
        self.assertEqual(res, custom_response)


if __name__ == '__main__':
    unittest.main()