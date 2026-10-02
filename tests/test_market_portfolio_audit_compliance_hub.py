import unittest
from unittest.mock import MagicMock, patch
import os
import uuid
import random
import io
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub

class TestMarketPortfolioAuditComplianceHub(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.mock_db = MagicMock()
        self.mock_exporter = MagicMock()
        self.hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.mock_db,
            audit_exporter=self.mock_exporter
        )

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_init_default_fallbacks(self):
        with patch('skills.market_portfolio_audit_compliance_hub.MarketParser') as mock_parser_cls, \
             patch('skills.market_portfolio_audit_compliance_hub.PortfolioAuditLogExporter') as mock_exporter_cls:
            
            random_file = f"{uuid.uuid4().hex}.db"
            hub = MarketPortfolioAuditComplianceHub(storage_file=random_file)
            
            mock_parser_cls.assert_called_once_with(random_file)
            mock_exporter_cls.assert_called_once_with(random_file)
            self.assertIsNotNone(hub.db_storage)
            self.assertIsNotNone(hub.audit_exporter)

    def test_run_compliance_export_success(self):
        expected_result = random.choice([True, {"status": uuid.uuid4().hex}])
        self.mock_exporter.export_audit_logs.return_value = expected_result
        
        export_path = f"{uuid.uuid4().hex}.log"
        res = self.hub.run_compliance_export(export_path)
        
        self.assertEqual(res, expected_result)
        self.mock_exporter.export_audit_logs.assert_called_once_with(export_path)

    def test_run_compliance_export_fallback_creates_file(self):
        self.mock_exporter.export_audit_logs.return_value = False
        export_path = f"{uuid.uuid4().hex}_{random.randint(1000, 9999)}.json"
        
        self.assertFalse(os.path.exists(export_path))
        
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

    def test_check_compliance_integrity(self):
        integrity_val = random.choice([True, False])
        self.mock_exporter.verify_log_integrity.return_value = integrity_val
        
        res = self.hub.check_compliance_integrity()
        self.assertEqual(res, integrity_val)

        self.mock_exporter.verify_log_integrity.return_value = None
        res_none = self.hub.check_compliance_integrity()
        self.assertTrue(res_none)

    def test_fetch_compliance_summary(self):
        summary_data = {uuid.uuid4().hex: random.randint(1, 100)}
        self.mock_exporter.get_audit_stream_summary.return_value = summary_data
        
        res = self.hub.fetch_compliance_summary()
        self.assertEqual(res, summary_data)
        self.mock_exporter.get_audit_stream_summary.assert_called_once()

    def test_process_audit_stream_data(self):
        export_path = f"{uuid.uuid4().hex}.dat"
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        stream_result = random.choice([True, False, None])
        self.mock_exporter.process_audit_stream.return_value = stream_result

        res = self.hub.process_audit_stream_data(export_path, stream_data)
        if stream_result is None:
            self.assertTrue(res)
        else:
            self.assertEqual(res, stream_result)
        self.mock_exporter.process_audit_stream.assert_called_once_with(export_path, stream_data)

    def test_generate_compliance_log(self):
        export_path = f"{uuid.uuid4().hex}.log"
        gen_result = random.choice([True, False, None])
        self.mock_exporter.generate_audit_log.return_value = gen_result

        res = self.hub.generate_compliance_log(export_path)
        if gen_result is None:
            self.assertTrue(res)
        else:
            self.assertEqual(res, gen_result)
        self.mock_exporter.generate_audit_log.assert_called_once_with(export_path)

    def test_audit_fetch_market_price(self):
        url = f"https://{uuid.uuid4().hex}.market/api/v1/price"
        expected_price = round(random.uniform(10.0, 1000.0), 2)
        self.mock_db.fetch_price.return_value = expected_price

        res = self.hub.audit_fetch_market_price(url)
        self.assertEqual(res, expected_price)
        self.mock_db.fetch_price.assert_called_once_with(url)

    def test_load_historical_audit_data(self):
        filename = f"{uuid.uuid4().hex}.csv"
        historical_records = [{uuid.uuid4().hex: uuid.uuid4().hex}]
        self.mock_db.load_data.return_value = historical_records

        res = self.hub.load_historical_audit_data(filename)
        self.assertEqual(res, historical_records)
        self.mock_db.load_data.assert_called_once_with(filename)

    def test_get_audit_stream_summary(self):
        summary_mock = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_exporter.get_audit_stream_summary.return_value = summary_mock

        res = self.hub.get_audit_stream_summary()
        self.assertEqual(res, summary_mock)

    def test_verify_log_integrity(self):
        self.mock_exporter.verify_log_integrity.return_value = None
        self.assertTrue(self.hub.verify_log_integrity())

        self.mock_exporter.verify_log_integrity.return_value = False
        self.assertFalse(self.hub.verify_log_integrity())

    def test_export_audit_logs(self):
        export_path = f"{uuid.uuid4().hex}.export"
        self.mock_exporter.export_audit_logs.return_value = None
        
        try:
            res = self.hub.export_audit_logs(export_path)
            self.assertTrue(res)
            self.assertTrue(os.path.exists(export_path))
        finally:
            if os.path.exists(export_path):
                os.remove(export_path)

    def test_exceptions_not_suppressed(self):
        error_msg = uuid.uuid4().hex
        self.mock_exporter.export_audit_logs.side_effect = RuntimeError(error_msg)
        
        with self.assertRaises(RuntimeError) as ctx:
            self.hub.run_compliance_export(f"{uuid.uuid4().hex}.err")
        self.assertIn(error_msg, str(ctx.exception))

if __name__ == '__main__':
    unittest.main()