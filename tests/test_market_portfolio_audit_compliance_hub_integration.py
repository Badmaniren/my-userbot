import unittest
import os
import uuid
import tempfile
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub

class TestMarketPortfolioAuditComplianceHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4()}.json")
        self.export_path = os.path.join(self.test_dir.name, f"audit_export_{uuid.uuid4()}.json")
        self.hub = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_compliance_export_and_integrity(self):
        random_stream_data = f"audit_stream_payload_{uuid.uuid4()}"
        
        export_result = self.hub.run_compliance_export(self.export_path)
        self.assertTrue(export_result)
        self.assertTrue(os.path.exists(self.export_path))

        stream_result = self.hub.process_audit_stream_data(self.export_path, random_stream_data)
        self.assertTrue(stream_result)

        integrity_result = self.hub.check_compliance_integrity()
        self.assertTrue(integrity_result)

        summary = self.hub.fetch_compliance_summary()
        self.assertIsNotNone(summary)

    def test_integration_historical_data_loading(self):
        history_file = os.path.join(self.test_dir.name, f"history_{uuid.uuid4()}.json")
        data = self.hub.load_historical_audit_data(history_file)
        self.assertTrue(os.path.exists(history_file))
        self.assertIsInstance(data, (list, dict, type(None)))

    def test_integration_market_price_audit(self):
        random_url = f"https://example.com/api/v1/asset/{uuid.uuid4()}"
        price = self.hub.audit_fetch_market_price(random_url)
        self.assertIsInstance(price, float)

if __name__ == "__main__":
    unittest.main()