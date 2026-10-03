import os
import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub


class TestMarketPortfolioAuditComplianceHub(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.db_storage_mock = MagicMock()
        self.audit_exporter_mock = MagicMock()
        self.hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.db_storage_mock,
            audit_exporter=self.audit_exporter_mock
        )

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_run_compliance_export_success(self):
        export_path = f"{uuid.uuid4().hex}.log"
        expected_result = ''.join(random.choices(string.ascii_letters, k=10))
        self.audit_exporter_mock.export_audit_logs.return_value = expected_result

        res = self.hub.run_compliance_export(export_path)

        self.assertEqual(res, expected_result)
        self.audit_exporter_mock.export_audit_logs.assert_called_once_with(export_path)

    def test_run_compliance_export_fallback_creates_file(self):
        export_path = f"{uuid.uuid4().hex}.json"
        self.audit_exporter_mock.export_audit_logs.return_value = False

        if os.path.exists(export_path):
            os.remove(export_path)

        res = self.hub.run_compliance_export(export_path)

        self.assertTrue(res)
        self.assertTrue(os.path.exists(export_path))
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "{}")

        if os.path.exists(export_path):
            os.remove(export_path)

    def test_check_compliance_integrity_none_returns_true(self):
        self.audit_exporter_mock.verify_log_integrity.return_value = None

        res = self.hub.check_compliance_integrity()

        self.assertTrue(res)
        self.audit_exporter_mock.verify_log_integrity.assert_called_once()

    def test_check_compliance_integrity_boolean(self):
        expected_val = random.choice([True, False])
        self.audit_exporter_mock.verify_log_integrity.return_value = expected_val

        res = self.hub.check_compliance_integrity()

        self.assertEqual(res, expected_val)

    def test_fetch_compliance_summary(self):
        expected_summary = {uuid.uuid4().hex: random.randint(1, 100)}
        self.audit_exporter_mock.get_audit_stream_summary.return_value = expected_summary

        res = self.hub.fetch_compliance_summary()

        self.assertEqual(res, expected_summary)
        self.audit_exporter_mock.get_audit_stream_summary.assert_called_once()

    def test_process_audit_stream_data(self):
        export_path = f"{uuid.uuid4().hex}.dat"
        stream_data = uuid.uuid4().hex
        self.audit_exporter_mock.process_audit_stream.return_value = None

        res = self.hub.process_audit_stream_data(export_path, stream_data)

        self.assertTrue(res)
        self.audit_exporter_mock.process_audit_stream.assert_called_once_with(export_path, stream_data)

    def test_generate_compliance_log(self):
        export_path = f"{uuid.uuid4().hex}.log"
        self.audit_exporter_mock.generate_audit_log.return_value = None

        res = self.hub.generate_compliance_log(export_path)

        self.assertTrue(res)
        self.audit_exporter_mock.generate_audit_log.assert_called_once_with(export_path)

    def test_audit_fetch_market_price_success(self):
        url = f"https://{uuid.uuid4().hex}.com/api"
        expected_price = round(random.uniform(10.0, 1000.0), 2)
        self.db_storage_mock.fetch_price.return_value = expected_price

        res = self.hub.audit_fetch_market_price(url)

        self.assertEqual(res, expected_price)
        self.db_storage_mock.fetch_price.assert_called_once_with(url)

    def test_audit_fetch_market_price_exception_handling(self):
        url = f"https://{uuid.uuid4().hex}.com/error"
        self.db_storage_mock.fetch_price.side_effect = Exception(uuid.uuid4().hex)

        res = self.hub.audit_fetch_market_price(url)

        self.assertEqual(res, 0.0)

    def test_load_historical_audit_data_file_missing(self):
        filename = f"{uuid.uuid4().hex}.json"
        expected_data = [uuid.uuid4().hex, uuid.uuid4().hex]
        self.db_storage_mock.load_data.return_value = expected_data

        if os.path.exists(filename):
            os.remove(filename)

        res = self.hub.load_historical_audit_data(filename)

        self.assertEqual(res, expected_data)
        self.assertTrue(os.path.exists(filename))
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "[]")

        if os.path.exists(filename):
            os.remove(filename)

    def test_get_audit_stream_summary(self):
        expected_summary = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.audit_exporter_mock.get_audit_stream_summary.return_value = expected_summary

        res = self.hub.get_audit_stream_summary()

        self.assertEqual(res, expected_summary)

    def test_verify_log_integrity(self):
        self.audit_exporter_mock.verify_log_integrity.return_value = None

        res = self.hub.verify_log_integrity()

        self.assertTrue(res)

    def test_export_audit_logs(self):
        export_path = f"{uuid.uuid4().hex}.json"
        self.audit_exporter_mock.export_audit_logs.return_value = None

        if os.path.exists(export_path):
            os.remove(export_path)

        res = self.hub.export_audit_logs(export_path)

        self.assertTrue(res)
        self.assertTrue(os.path.exists(export_path))

        if os.path.exists(export_path):
            os.remove(export_path)

    def test_init_default_fallback_attributes(self):
        with patch('skills.market_portfolio_audit_compliance_hub.MarketParser') as mock_parser_cls, \
             patch('skills.market_portfolio_audit_compliance_hub.PortfolioAuditLogExporter') as mock_exporter_cls:
            
            mock_exporter_instance = MagicMock()
            del mock_exporter_instance.process_audit_stream
            del mock_exporter_instance.generate_audit_log
            mock_exporter_cls.return_value = mock_exporter_instance

            hub = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)

            self.assertTrue(hasattr(hub.audit_exporter, 'process_audit_stream'))
            self.assertTrue(hasattr(hub.audit_exporter, 'generate_audit_log'))
            self.assertTrue(hub.audit_exporter.process_audit_stream('path', 'stream'))
            self.assertTrue(hub.audit_exporter.generate_audit_log('path'))