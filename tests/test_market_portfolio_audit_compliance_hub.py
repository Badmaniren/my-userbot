import unittest
from unittest.mock import MagicMock, patch
import os
import uuid
import random
import string
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub

class TestMarketPortfolioAuditComplianceHub(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.export_path = f"{uuid.uuid4().hex}.json"
        self.url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        self.stream_data = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        
        self.mock_db = MagicMock()
        self.mock_exporter = MagicMock()
        
        self.hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.mock_db,
            audit_exporter=self.mock_exporter
        )

    def tearDown(self):
        for path in [self.storage_file, self.export_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_init_default_components(self):
        with patch('skills.market_portfolio_audit_compliance_hub.MarketParser') as mp_mock, \
             with_exporter := patch('skills.market_portfolio_audit_compliance_hub.PortfolioAuditLogExporter') as pae_mock:
            with mp_mock, pae_mock:
                hub = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)
                self.assertIsNotNone(hub.db_storage)
                self.assertIsNotNone(hub.audit_exporter)

    def test_run_compliance_export_success(self):
        expected_result = random.choice([True, False, {"status": uuid.uuid4().hex}])
        self.mock_exporter.export_audit_logs.return_value = expected_result
        
        result = self.hub.run_compliance_export(self.export_path)
        self.assertEqual(result, expected_result)
        self.mock_exporter.export_audit_logs.assert_called_once_with(self.export_path)

    def test_run_compliance_export_fallback(self):
        self.mock_exporter.export_audit_logs.return_value = False
        
        result = self.hub.run_compliance_export(self.export_path)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.export_path))
        
        with open(self.export_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "{}")

    def test_check_compliance_integrity(self):
        expected_res = random.choice([True, False])
        self.mock_exporter.verify_log_integrity.return_value = expected_res
        
        result = self.hub.check_compliance_integrity()
        self.assertEqual(result, expected_res)

        self.mock_exporter.verify_log_integrity.return_value = None
        result_none = self.hub.check_compliance_integrity()
        self.assertTrue(result_none)

    def test_fetch_compliance_summary(self):
        expected_summary = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_exporter.get_audit_stream_summary.return_value = expected_summary
        
        result = self.hub.fetch_compliance_summary()
        self.assertEqual(result, expected_summary)

    def test_process_audit_stream_data(self):
        expected_res = random.choice([True, False])
        self.mock_exporter.process_audit_stream.return_value = expected_res
        
        result = self.hub.process_audit_stream_data(self.export_path, self.stream_data)
        self.assertEqual(result, expected_res)
        self.mock_exporter.process_audit_stream.assert_called_once_with(self.export_path, self.stream_data)

    def test_generate_compliance_log(self):
        expected_res = random.choice([True, False])
        self.mock_exporter.generate_audit_log.return_value = expected_res
        
        result = self.hub.generate_compliance_log(self.export_path)
        self.assertEqual(result, expected_res)
        self.mock_exporter.generate_audit_log.assert_called_once_with(self.export_path)

    def test_audit_fetch_market_price_success(self):
        expected_price = round(random.uniform(10.0, 1000.0), 2)
        self.mock_db.fetch_price.return_value = expected_price
        
        price = self.hub.audit_fetch_market_price(self.url)
        self.assertEqual(price, expected_price)
        self.mock_db.fetch_price.assert_called_once_with(self.url)

    def test_audit_fetch_market_price_exception_handling(self):
        class ComplianceMarketError(Exception):
            pass

        self.mock_db.fetch_price.side_effect = ComplianceMarketError(uuid.uuid4().hex)
        
        price = self.hub.audit_fetch_market_price(self.url)
        self.assertEqual(price, 0.0)

    def test_load_historical_audit_data_existing(self):
        expected_data = [uuid.uuid4().hex, uuid.uuid4().hex]
        self.mock_db.load_data.return_value = expected_data
        
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("[]")

        result = self.hub.load_historical_audit_data(self.storage_file)
        self.assertEqual(result, expected_data)
        self.mock_db.load_data.assert_called_once_with(self.storage_file)

    def test_load_historical_audit_data_missing(self):
        missing_file = f"{uuid.uuid4().hex}.json"
        expected_data = []
        self.mock_db.load_data.return_value = expected_data
        
        self.assertFalse(os.path.exists(missing_file))
        result = self.hub.load_historical_audit_data(missing_file)
        
        self.assertTrue(os.path.exists(missing_file))
        with open(missing_file, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "[]")
        
        os.remove(missing_file)

    def test_get_audit_stream_summary(self):
        expected_summary = {uuid.uuid4().hex: random.randint(1, 100)}
        self.mock_exporter.get_audit_stream_summary.return_value = expected_summary
        
        result = self.hub.get_audit_stream_summary()
        self.assertEqual(result, expected_summary)

    def test_verify_log_integrity(self):
        self.mock_exporter.verify_log_integrity.return_value = None
        self.assertTrue(self.hub.verify_log_integrity())
        
        self.mock_exporter.verify_log_integrity.return_value = False
        self.assertFalse(self.hub.verify_log_integrity())

    def test_export_audit_logs(self):
        self.mock_exporter.export_audit_logs.return_value = True
        self.assertTrue(self.hub.export_audit_logs(self.export_path))
        
        self.mock_exporter.export_audit_logs.return_value = None
        self.assertTrue(self.hub.export_audit_logs(self.export_path))
        self.assertTrue(os.path.exists(self.export_path))

if __name__ == '__main__':
    unittest.main()