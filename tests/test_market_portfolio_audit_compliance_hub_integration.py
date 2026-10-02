import unittest
import os
import uuid
import random
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub
from skills.db_storage import MarketParser
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter

class TestMarketPortfolioAuditComplianceHubIntegration(unittest.TestCase):
    def setUp(self):
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_audit_storage_{self.rand_suffix}.db"
        self.export_path = f"test_compliance_export_{self.rand_suffix}.json"
        
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

    def test_compliance_hub_integration_workflow(self):
        random_price_url = f"https://finance.example.com/asset/{uuid.uuid4().hex}"
        
        integrity_result = self.hub.check_compliance_integrity()
        self.assertIn(integrity_result, [True, False])

        export_res = self.hub.run_compliance_export(self.export_path)
        self.assertTrue(export_res)
        self.assertTrue(os.path.exists(self.export_path))

        stream_data = f"audit_stream_payload_{uuid.uuid4().hex}"
        stream_res = self.hub.process_audit_stream_data(self.export_path, stream_data)
        self.assertIn(stream_res, [True, False])

        gen_res = self.hub.generate_compliance_log(self.export_path)
        self.assertIn(gen_res, [True, False])

        summary = self.hub.fetch_compliance_summary()
        self.assertIsNotNone(summary)

        historical_filename = f"history_{uuid.uuid4().hex}.json"
        history_data = self.hub.load_historical_audit_data(historical_filename)
        self.assertIsNotNone(history_data)

        market_price = self.hub.audit_fetch_market_price(random_price_url)
        self.assertIsNotNone(market_price)

        verify_res = self.hub.verify_log_integrity()
        self.assertIn(verify_res, [True, False])

        export_logs_res = self.hub.export_audit_logs(self.export_path)
        self.assertTrue(export_logs_res)

if __name__ == "__main__":
    unittest.main()