import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import io

from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub


class TestMarketPortfolioAuditComplianceHub(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.export_path = f"{uuid.uuid4().hex}.json"
        self.history_file = f"{uuid.uuid4().hex}.json"
        self.url = f"https://{uuid.uuid4().hex}.com/market"
        self.stream_name = uuid.uuid4().hex

    def tearDown(self):
        for f in [self.storage_file, self.export_path, self.history_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass

    def test_init_default_components(self):
        with patch('skills.market_portfolio_audit_compliance_hub.MarketParser') as mp_mock, \
             patch('skills.market_portfolio_audit_compliance_hub.PortfolioAuditLogExporter') as pae_mock:
            
            hub = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)
            mp_mock.assert_called_once_with(self.storage_file)
            pae_mock.assert_called_once_with(self.storage_file)
            self.assertIsNotNone(hub.db_storage)
            self.assertIsNotNone(hub.audit_exporter)

    def test_init_custom_components(self):
        db_mock = MagicMock()
        exporter_mock = MagicMock()
        del exporter_mock.process_audit_stream
        del exporter_mock.generate_audit_log

        hub = MarketPortfolioAuditComplianceHub(db_storage=db_mock, audit_exporter=exporter_mock)
        self.assertEqual(hub.db_storage, db_mock)
        self.assertEqual(hub.audit_exporter, exporter_mock)
        self.assertTrue(hasattr(hub.audit_exporter, 'process_audit_stream'))
        self.assertTrue(hasattr(hub.audit_exporter, 'generate_audit_log'))

    def test_run_compliance_export_success(self):
        expected_res = random.choice([True, {"status": uuid.uuid4().hex}])
        exporter_mock = MagicMock()
        exporter_mock.export_audit_logs.return_value = expected_res

        hub = MarketPortfolioAuditComplianceHub(audit_exporter=exporter_mock)
        res = hub.run_compliance_export(self.export_path)
        self.assertEqual(res, expected_res)
        exporter_mock.export_audit_logs.assert_called_once_with(self.export_path)

    def test_run_compliance_export_fallback(self):
        exporter_mock = MagicMock()
        exporter_mock.export_audit_logs.return_value = False

        hub = MarketPortfolioAuditComplianceHub(audit_exporter=exporter_mock)
        res = hub.run_compliance_export(self.export_path)
        self.assertTrue(res)
        self.assertTrue(os.path.exists(self.export_path))
        with open(self.export_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "{}")

    def test_check_compliance_integrity_none_to_true(self):
        exporter_mock = MagicMock()
        exporter_mock.verify_log_integrity.return_value = None

        hub = MarketPortfolioAuditComplianceHub(audit_exporter=exporter_mock)
        res = hub.check_compliance_integrity()
        self.assertTrue(res)

    def test_check_compliance_integrity_explicit(self):
        expected = random.choice([True, False])
        exporter_mock = MagicMock()
        exporter_mock.verify_log_integrity.return_value = expected

        hub = MarketPortfolioAuditComplianceHub(audit_exporter=exporter_mock)
        res = hub.check_compliance_integrity()
        self.assertEqual(res, expected)

    def test_fetch_compliance_summary(self):
        summary_data = {uuid.uuid4().hex: random.randint(1, 100)}
        exporter_mock = MagicMock()
        exporter_mock.get_audit_stream_summary.return_value = summary_data

        hub = MarketPortfolioAuditComplianceHub(audit_exporter=exporter_mock)
        res = hub.fetch_compliance_summary()
        self.assertEqual(res, summary_data)

    def test_process_audit_stream_data_none_to_true(self):
        exporter_mock = MagicMock()
        exporter_mock.process_audit_stream.return_value = None

        hub = MarketPortfolioAuditComplianceHub(audit_exporter=exporter_mock)
        res = hub.process_audit_stream_data(self.export_path, self.stream_name)
        self.assertTrue(res)
        exporter_mock.process_audit_stream.assert_called_once_with(self.export_path, self.stream_name)

    def test_generate_compliance_log_none_to_true(self):
        exporter_mock = MagicMock()
        exporter_mock.generate_audit_log.return_value = None

        hub = MarketPortfolioAuditComplianceHub(audit_exporter=exporter_mock)
        res = hub.generate_compliance_log(self.export_path)
        self.assertTrue(res)
        exporter_mock.generate_audit_log.assert_called_once_with(self.export_path)

    def test_audit_fetch_market_price_success(self):
        expected_price = round(random.uniform(10.0, 1000.0), 2)
        db_mock = MagicMock()
        db_mock.fetch_price.return_value = expected_price

        hub = MarketPortfolioAuditComplianceHub(db_storage=db_mock)
        res = hub.audit_fetch_market_price(self.url)
        self.assertEqual(res, expected_price)
        db_mock.fetch_price.assert_called_once_with(self.url)

    def test_audit_fetch_market_price_handled_exceptions(self):
        exceptions_to_test = [
            ValueError, TypeError, KeyError, AttributeError,
            RuntimeError, ConnectionError, IOError
        ]
        for exc_cls in exceptions_to_test:
            db_mock = MagicMock()
            db_mock.fetch_price.side_effect = exc_cls(uuid.uuid4().hex)

            hub = MarketPortfolioAuditComplianceHub(db_storage=db_mock)
            res = hub.audit_fetch_market_price(self.url)
            self.assertEqual(res, 0.0)

    def test_audit_fetch_market_price_unhandled_exception(self):
        db_mock = MagicMock()
        db_mock.fetch_price.side_effect = MemoryError(uuid.uuid4().hex)

        hub = MarketPortfolioAuditComplianceHub(db_storage=db_mock)
        with self.assertRaises(MemoryError):
            hub.audit_fetch_market_price(self.url)

    def test_load_historical_audit_data_file_creation(self):
        expected_data = [uuid.uuid4().hex, random.randint(1, 50)]
        db_mock = MagicMock()
        db_mock.load_data.return_value = expected_data

        hub = MarketPortfolioAuditComplianceHub(db_storage=db_mock)
        res = hub.load_historical_audit_data(self.history_file)
        self.assertEqual(res, expected_data)
        self.assertTrue(os.path.exists(self.history_file))
        with open(self.history_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "[]")
        db_mock.load_data.assert_called_once_with(self.history_file)

    def test_get_audit_stream_summary(self):
        summary = {uuid.uuid4().hex: uuid.uuid4().hex}
        exporter_mock = MagicMock()
        exporter_mock.get_audit_stream_summary.return_value = summary

        hub = MarketPortfolioAuditComplianceHub(audit_exporter=exporter_mock)
        self.assertEqual(hub.get_audit_stream_summary(), summary)

    def test_verify_log_integrity(self):
        exporter_mock = MagicMock()
        exporter_mock.verify_log_integrity.return_value = None

        hub = MarketPortfolioAuditComplianceHub(audit_exporter=exporter_mock)
        self.assertTrue(hub.verify_log_integrity())

    def test_export_audit_logs_fallback(self):
        exporter_mock = MagicMock()
        exporter_mock.export_audit_logs.return_value = None

        hub = MarketPortfolioAuditComplianceHub(audit_exporter=exporter_mock)
        self.assertTrue(hub.export_audit_logs(self.export_path))
        self.assertTrue(os.path.exists(self.export_path))
        with open(self.export_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "{}")