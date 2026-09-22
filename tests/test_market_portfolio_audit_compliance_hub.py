import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import io

from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub


class TestMarketPortfolioAuditComplianceHub(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.export_path = f"export_{uuid.uuid4().hex}.log"
        self.url = f"https://example.com/market/{uuid.uuid4().hex}"
        self.symbol = f"SYM_{uuid.uuid4().hex[:5]}"
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.hub = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)

    def tearDown(self):
        for path in [self.storage_file, self.export_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_init_default_dependencies(self):
        hub = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)
        self.assertIsNotNone(hub.db_storage)
        self.assertIsNotNone(hub.audit_exporter)

    def test_init_injected_dependencies(self):
        mock_db = MagicMock()
        mock_exporter = MagicMock()
        hub = MarketPortfolioAuditComplianceHub(db_storage=mock_db, audit_exporter=mock_exporter)
        self.assertEqual(hub.db_storage, mock_db)
        self.assertEqual(hub.audit_exporter, mock_exporter)

    def test_run_compliance_export_success(self):
        with patch.object(self.hub.audit_exporter, 'export_audit_logs', return_value=None) as mock_export:
            res = self.hub.run_compliance_export(self.export_path)
            mock_export.assert_called_once_with(self.export_path)
            self.assertTrue(res)

    def test_run_compliance_export_boolean(self):
        expected = True
        with patch.object(self.hub.audit_exporter, 'export_audit_logs', return_value=expected) as mock_export:
            res = self.hub.run_compliance_export(self.export_path)
            mock_export.assert_called_once_with(self.export_path)
            self.assertEqual(res, expected)

    def test_check_compliance_integrity(self):
        expected = random.choice([True, False])
        with patch.object(self.hub.audit_exporter, 'verify_log_integrity', return_value=expected) as mock_verify:
            res = self.hub.check_compliance_integrity()
            mock_verify.assert_called_once()
            self.assertEqual(res, expected)

    def test_fetch_compliance_summary(self):
        expected_summary = {uuid.uuid4().hex: random.randint(1, 100)}
        with patch.object(self.hub.audit_exporter, 'get_audit_stream_summary', return_value=expected_summary) as mock_summary:
            res = self.hub.fetch_compliance_summary()
            mock_summary.assert_called_once()
            self.assertEqual(res, expected_summary)

    def test_process_audit_stream_data(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        expected = random.choice([True, False, None])
        with patch.object(self.hub.audit_exporter, 'process_audit_stream', return_value=expected) as mock_process:
            res = self.hub.process_audit_stream_data(self.export_path, stream_data)
            mock_process.assert_called_once_with(self.export_path, stream_data)
            if expected is None:
                self.assertTrue(res)
            else:
                self.assertEqual(res, expected)

    def test_generate_compliance_log(self):
        expected = random.choice([True, False, None])
        with patch.object(self.hub.audit_exporter, 'generate_audit_log', return_value=expected) as mock_gen:
            res = self.hub.generate_compliance_log(self.export_path)
            mock_gen.assert_called_once_with(self.export_path)
            if expected is None:
                self.assertTrue(res)
            else:
                self.assertEqual(res, expected)

    def test_audit_fetch_market_price(self):
        with patch.object(self.hub.db_storage, 'fetch_price', return_value=self.price) as mock_fetch:
            res = self.hub.audit_fetch_market_price(self.url)
            mock_fetch.assert_called_once_with(self.url)
            self.assertEqual(res, self.price)

    def test_load_historical_audit_data(self):
        filename = f"hist_{uuid.uuid4().hex}.json"
        expected_data = {uuid.uuid4().hex: self.price}
        with patch.object(self.hub.db_storage, 'load_data', return_value=expected_data) as mock_load:
            res = self.hub.load_historical_audit_data(filename)
            mock_load.assert_called_once_with(filename)
            self.assertEqual(res, expected_data)

    def test_get_audit_stream_summary(self):
        expected_summary = {uuid.uuid4().hex: uuid.uuid4().hex}
        with patch.object(self.hub.audit_exporter, 'get_audit_stream_summary', return_value=expected_summary) as mock_summary:
            res = self.hub.get_audit_stream_summary()
            mock_summary.assert_called_once()
            self.assertEqual(res, expected_summary)

    def test_verify_log_integrity(self):
        expected = random.choice([True, False, None])
        with patch.object(self.hub.audit_exporter, 'verify_log_integrity', return_value=expected) as mock_verify:
            res = self.hub.verify_log_integrity()
            mock_verify.assert_called_once()
            if expected is None:
                self.assertTrue(res)
            else:
                self.assertEqual(res, expected)

    def test_export_audit_logs_none_creates_file(self):
        with patch.object(self.hub.audit_exporter, 'export_audit_logs', return_value=None) as mock_export:
            if os.path.exists(self.export_path):
                os.remove(self.export_path)
            res = self.hub.export_audit_logs(self.export_path)
            mock_export.assert_called_once_with(self.export_path)
            self.assertTrue(res)
            self.assertTrue(os.path.exists(self.export_path))
            with open(self.export_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertEqual(content, "{}")

    def test_export_audit_logs_explicit_result(self):
        expected = True
        with patch.object(self.hub.audit_exporter, 'export_audit_logs', return_value=expected) as mock_export:
            res = self.hub.export_audit_logs(self.export_path)
            mock_export.assert_called_once_with(self.export_path)
            self.assertEqual(res, expected)