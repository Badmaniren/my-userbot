import unittest
import os
import uuid
import random
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub
from skills.db_storage import MarketParser
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter

class TestMarketPortfolioAuditComplianceHubIntegration(unittest.TestCase):
    def setUp(self):
        self.rand_str = str(uuid.uuid4())
        self.storage_file = f"test_storage_{self.rand_str}.json"
        self.export_path = f"test_export_{self.rand_str}.json"
        self.historical_file = f"test_historical_{self.rand_str}.json"
        
        self.db_storage = MarketParser(self.storage_file)
        self.audit_exporter = PortfolioAuditLogExporter(self.storage_file)
        self.hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.db_storage,
            audit_exporter=self.audit_exporter
        )

    def tearDown(self):
        for f in [self.storage_file, self.export_path, self.historical_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass

    def test_run_compliance_export_integration(self):
        res = self.hub.run_compliance_export(self.export_path)
        self.assertIsInstance(res, bool)
        self.assertTrue(os.path.exists(self.export_path))

    def test_check_compliance_integrity_integration(self):
        res = self.hub.check_compliance_integrity()
        self.assertIsInstance(res, bool)

    def test_fetch_compliance_summary_integration(self):
        summary = self.hub.fetch_compliance_summary()
        self.assertIsInstance(summary, dict)

    def test_process_audit_stream_data_integration(self):
        stream_data = {"event_id": str(uuid.uuid4()), "value": random.random()}
        res = self.hub.process_audit_stream_data(self.export_path, stream_data)
        self.assertIsInstance(res, bool)

    def test_generate_compliance_log_integration(self):
        res = self.hub.generate_compliance_log(self.export_path)
        self.assertIsInstance(res, bool)

    def test_audit_fetch_market_price_integration(self):
        random_url = f"http://example.com/price/{uuid.uuid4()}"
        price = self.hub.audit_fetch_market_price(random_url)
        self.assertIsInstance(price, float)

    def test_load_historical_audit_data_integration(self):
        data = self.hub.load_historical_audit_data(self.historical_file)
        self.assertIsInstance(data, list)
        self.assertTrue(os.path.exists(self.historical_file))

    def test_get_audit_stream_summary_integration(self):
        summary = self.hub.get_audit_stream_summary()
        self.assertIsInstance(summary, dict)

    def test_verify_log_integrity_integration(self):
        res = self.hub.verify_log_integrity()
        self.assertIsInstance(res, bool)

    def test_export_audit_logs_integration(self):
        res = self.hub.export_audit_logs(self.export_path)
        self.assertIsInstance(res, bool)
        self.assertTrue(os.path.exists(self.export_path))

if __name__ == "__main__":
    unittest.main()