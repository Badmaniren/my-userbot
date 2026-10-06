import unittest
import os
import uuid
import random
from skills.db_storage import MarketParser
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub


class TestMarketPortfolioAuditComplianceHubIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_id = str(uuid.uuid4())
        self.storage_file = f"test_storage_{self.unique_id}.json"
        self.export_file = f"test_export_{self.unique_id}.json"
        self.historical_file = f"test_history_{self.unique_id}.json"
        
        self.db_storage = MarketParser(self.storage_file)
        self.audit_exporter = PortfolioAuditLogExporter(self.storage_file)
        
        self.hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.db_storage,
            audit_exporter=self.audit_exporter
        )

    def tearDown(self):
        for f_path in [self.storage_file, self.export_file, self.historical_file]:
            if os.path.exists(f_path):
                try:
                    os.remove(f_path)
                except OSError:
                    pass

    def test_integration_compliance_export_and_integrity(self):
        rand_val = random.randint(1000, 9999)
        custom_export_path = f"export_{rand_val}_{self.export_file}"
        
        try:
            export_result = self.hub.run_compliance_export(custom_export_path)
            self.assertIn(export_result, [True, False])
            self.assertTrue(os.path.exists(custom_export_path))
            
            integrity_result = self.hub.check_compliance_integrity()
            self.assertIsInstance(integrity_result, bool)
            
            summary = self.hub.fetch_compliance_summary()
            self.assertIsNotNone(summary)
            
        finally:
            if os.path.exists(custom_export_path):
                os.remove(custom_export_path)

    def test_integration_historical_data_and_price_fetching(self):
        random_price = round(random.uniform(10.0, 1000.0), 2)
        test_url = f"http://example.com/asset/{self.unique_id}"
        
        loaded_data = self.hub.load_historical_audit_data(self.historical_file)
        self.assertIsNotNone(loaded_data)
        self.assertTrue(os.path.exists(self.historical_file))
        
        price = self.hub.audit_fetch_market_price(test_url)
        self.assertIsInstance(price, float)
        self.assertEqual(price, 0.0)

    def test_integration_stream_processing_and_generation(self):
        stream_data = {"audit_id": self.unique_id, "metric": random.random()}
        
        stream_res = self.hub.process_audit_stream_data(self.export_file, stream_data)
        self.assertIsInstance(stream_res, bool)
        
        gen_res = self.hub.generate_compliance_log(self.export_file)
        self.assertIsInstance(gen_res, bool)


if __name__ == "__main__":
    unittest.main()