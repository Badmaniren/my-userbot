import unittest
from unittest.mock import MagicMock, patch
import os
import uuid
import random
import string
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub


class TestMarketPortfolioAuditComplianceHub(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.mock_db_storage = MagicMock()
        self.mock_audit_exporter = MagicMock()
        self.hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.mock_db_storage,
            audit_exporter=self.mock_audit_exporter
        )

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_init_creates_default_instances(self):
        with patch('skills.market_portfolio_audit_compliance_hub.MarketParser') as MockParser, \
             patch('skills.market_portfolio_audit_compliance_hub.PortfolioAuditLogExporter') as MockExporter:
            
            rand_file = f"{uuid.uuid4().hex}.db"
            hub = MarketPortfolioAuditComplianceHub(storage_file=rand_file)
            
            MockParser.assert_called_once_with(rand_file)
            MockExporter.assert_called_once_with(rand_file)
            self.assertTrue(hasattr(hub.audit_exporter, 'process_audit_stream'))
            self.assertTrue(hasattr(hub.audit_exporter, 'generate_audit_log'))

    def test_run_compliance_export_success(self):
        export_path = f"{uuid.uuid4().hex}.log"
        expected_result = random.choice([True, {"status": uuid.uuid4().hex}])
        self.mock_audit_exporter.export_audit_logs.return_value = expected_result

        res = self.hub.run_compliance_export(export_path)
        self.assertEqual(res, expected_result)
        self.mock_audit_exporter.export_audit_logs.assert_called_once_with(export_path)

    def test_run_compliance_export_fallback_creates_file(self):
        export_path = f"{uuid.uuid4().hex}_missing.log"
        self.mock_audit_exporter.export_audit_logs.return_value = False

        try:
            res = self.hub.run_compliance_export(export_path)
            self.assertTrue(res)
            self.assertTrue(os.path.exists(export_path))
            with open(export_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertEqual(content, "{}")
        finally:
            if os.path.exists(export_path):
                os.remove(export_path)

    def test_check_compliance_integrity_none_returns_true(self):
        self.mock_audit_exporter.verify_log_integrity.return_value = None
        res = self.hub.check_compliance_integrity()
        self.assertTrue(res)

    def test_check_compliance_integrity_explicit_bool(self):
        expected = random.choice([True, False])
        self.mock_audit_exporter.verify_log_integrity.return_value = expected
        res = self.hub.check_compliance_integrity()
        self.assertEqual(res, expected)

    def test_fetch_compliance_summary(self):
        summary_data = {uuid.uuid4().hex: random.randint(1, 100)}
        self.mock_audit_exporter.get_audit_stream_summary.return_value = summary_data

        res = self.hub.fetch_compliance_summary()
        self.assertEqual(res, summary_data)
        self.mock_audit_exporter.get_audit_stream_summary.assert_called_once()

    def test_process_audit_stream_data(self):
        export_path = f"{uuid.uuid4().hex}.dat"
        stream_data = uuid.uuid4().bytes
        self.mock_audit_exporter.process_audit_stream.return_value = None

        res = self.hub.process_audit_stream_data(export_path, stream_data)
        self.assertTrue(res)
        self.mock_audit_exporter.process_audit_stream.assert_called_once_with(export_path, stream_data)

    def test_generate_compliance_log(self):
        export_path = f"{uuid.uuid4().hex}.log"
        self.mock_audit_exporter.generate_audit_log.return_value = None

        res = self.hub.generate_compliance_log(export_path)
        self.assertTrue(res)
        self.mock_audit_exporter.generate_audit_log.assert_called_once_with(export_path)

    def test_audit_fetch_market_price(self):
        url = f"https://{uuid.uuid4().hex}.market/api/v1/price"
        expected_price = round(random.uniform(10.0, 1000.0), 2)
        self.mock_db_storage.fetch_price.return_value = expected_price

        res = self.hub.audit_fetch_market_price(url)
        self.assertEqual(res, expected_price)
        self.mock_db_storage.fetch_price.assert_called_once_with(url)

    def test_load_historical_audit_data(self):
        filename = f"{uuid.uuid4().hex}_hist.json"
        historical_records = [{uuid.uuid4().hex: uuid.uuid4().hex} for _ in range(3)]
        self.mock_db_storage.load_data.return_value = historical_records

        res = self.hub.load_historical_audit_data(filename)
        self.assertEqual(res, historical_records)
        self.mock_db_storage.load_data.assert_called_once_with(filename)

    def test_get_audit_stream_summary(self):
        summary = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_audit_exporter.get_audit_stream_summary.return_value = summary

        res = self.hub.get_audit_stream_summary()
        self.assertEqual(res, summary)

    def test_verify_log_integrity_delegation(self):
        expected_integrity = random.choice([True, False])
        self.mock_audit_exporter.verify_log_integrity.return_value = expected_integrity

        res = self.hub.verify_log_integrity()
        self.assertEqual(res, expected_integrity)

    def test_export_audit_logs_delegation(self):
        export_path = f"{uuid.uuid4().hex}_export.log"
        expected_outcome = {uuid.uuid4().hex: random.randint(1, 50)}
        self.mock_audit_exporter.export_audit_logs.return_value = expected_outcome

        res = self.hub.export_audit_logs(export_path)
        self.assertEqual(res, expected_outcome)
        self.mock_audit_exporter.export_audit_logs.assert_called_once_with(export_path)


if __name__ == "__main__":
    unittest.main()