import unittest
import os
import uuid
import random
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub
from skills.db_storage import MarketParser
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter

class TestMarketPortfolioAuditComplianceHubIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_id = str(uuid.uuid4())
        self.storage_file = f"test_audit_storage_{self.unique_id}.json"
        self.export_path = f"test_compliance_export_{self.unique_id}.json"
        
        self.db_storage = MarketParser(self.storage_file)
        self.audit_exporter = PortfolioAuditLogExporter(self.storage_file)
        
        self.hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.db_storage,
            audit_exporter=self.audit_exporter
        )

    def tearDown(self):
        for path in [self.storage_file, self.export_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_compliance_export_integration(self):
        random_payload = f"audit_stream_{uuid.uuid4()}"
        result = self.hub.run_compliance_export(self.export_path)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.export_path))

    def test_historical_audit_data_integration(self):
        test_filename = f"history_{uuid.uuid4()}.json"
        try:
            res = self.hub.load_historical_audit_data(test_filename)
            self.assertTrue(os.path.exists(test_filename))
        finally:
            if os.path.exists(test_filename):
                os.remove(test_filename)

    def test_audit_fetch_market_price_exception_handling(self):
        invalid_url = f"invalid_protocol://{uuid.uuid4()}.local"
        price = self.hub.audit_fetch_market_price(invalid_url)
        self.assertEqual(price, 0.0)

    def test_compliance_integrity_and_summary(self):
        integrity = self.hub.check_compliance_integrity()
        self.assertIsNotNone(integrity)
        
        summary = self.hub.fetch_compliance_summary()
        self.assertIsNotNone(summary)

if __name__ == "__main__":
    unittest.main()