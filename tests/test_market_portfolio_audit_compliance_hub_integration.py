import unittest
import os
import uuid
import tempfile
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub
from skills.db_storage import MarketParser
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter

class TestMarketPortfolioAuditComplianceHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.rand_str = str(uuid.uuid4())
        self.storage_file = os.path.join(self.test_dir.name, f"storage_{self.rand_str}.json")
        self.export_path = os.path.join(self.test_dir.name, f"export_{self.rand_str}.json")
        self.history_file = os.path.join(self.test_dir.name, f"history_{self.rand_str}.json")

        self.db_storage = MarketParser(self.storage_file)
        self.audit_exporter = PortfolioAuditLogExporter(self.storage_file)
        
        self.hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.db_storage,
            audit_exporter=self.audit_exporter
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_compliance_export_and_integrity(self):
        res_export = self.hub.run_compliance_export(self.export_path)
        self.assertTrue(res_export)
        self.assertTrue(os.path.exists(self.export_path))

        res_integrity = self.hub.check_compliance_integrity()
        self.assertIsNotNone(res_integrity)

    def test_integration_market_price_audit_exception_handling(self):
        invalid_url = f"http://invalid-url-{uuid.uuid4()}.local/price"
        price = self.hub.audit_fetch_market_price(invalid_url)
        self.assertEqual(price, 0.0)

    def test_integration_historical_audit_data_loading(self):
        data = self.hub.load_historical_audit_data(self.history_file)
        self.assertTrue(os.path.exists(self.history_file))
        self.assertIsInstance(data, (list, dict))

    def test_integration_compliance_summary_and_streams(self):
        stream_data = f"audit_stream_{uuid.uuid4()}"
        res_stream = self.hub.process_audit_stream_data(self.export_path, stream_data)
        self.assertTrue(res_stream)

        summary = self.hub.fetch_compliance_summary()
        self.assertIsNotNone(summary)

        log_res = self.hub.generate_compliance_log(self.export_path)
        self.assertTrue(log_res)

        verify_res = self.hub.verify_log_integrity()
        self.assertIsNotNone(verify_res)

        export_logs_res = self.hub.export_audit_logs(self.export_path)
        self.assertTrue(export_logs_res)

if __name__ == "__main__":
    unittest.main()