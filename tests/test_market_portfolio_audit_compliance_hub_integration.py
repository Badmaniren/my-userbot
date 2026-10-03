import unittest
import os
import tempfile
import uuid
import random
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub
from skills.db_storage import MarketParser
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter

class TestMarketPortfolioAuditComplianceHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4().hex}.json")
        self.export_path = os.path.join(self.test_dir.name, f"audit_export_{uuid.uuid4().hex}.json")
        
        self.db_storage = MarketParser(self.storage_file)
        self.audit_exporter = PortfolioAuditLogExporter(self.storage_file)
        
        self.hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.db_storage,
            audit_exporter=self.audit_exporter
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_compliance_export_and_integrity_integration(self):
        random_id = str(uuid.uuid4())
        test_stream = {"audit_id": random_id, "metric": random.uniform(10.0, 1000.0)}
        
        process_res = self.hub.process_audit_stream_data(self.export_path, test_stream)
        self.assertTrue(process_res)

        export_res = self.hub.run_compliance_export(self.export_path)
        self.assertTrue(export_res)
        self.assertTrue(os.path.exists(self.export_path))

        integrity_res = self.hub.check_compliance_integrity()
        self.assertIsInstance(integrity_res, bool)

        summary = self.hub.fetch_compliance_summary()
        self.assertIsNotNone(summary)

    def test_historical_audit_data_loading(self):
        random_filename = os.path.join(self.test_dir.name, f"history_{uuid.uuid4().hex}.json")
        data = self.hub.load_historical_audit_data(random_filename)
        
        self.assertTrue(os.path.exists(random_filename))
        self.assertIsInstance(data, (list, dict))

    def test_market_price_fetching_fallback(self):
        random_url = f"http://localhost:{random.randint(1000, 9999)}/{uuid.uuid4().hex}"
        price = self.hub.audit_fetch_market_price(random_url)
        self.assertIsInstance(price, float)

if __name__ == "__main__":
    unittest.main()