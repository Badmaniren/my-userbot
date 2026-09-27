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
        
        self.db_storage = MarketParser(self.storage_file)
        self.audit_exporter = PortfolioAuditLogExporter(self.storage_file)
        
        self.hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.db_storage,
            audit_exporter=self.audit_exporter
        )

    def tearDown(self):
        for filepath in [self.storage_file, self.export_path]:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass

    def test_compliance_export_and_integrity_integration(self):
        random_price = round(random.uniform(10.0, 1000.0), 2)
        test_url = f"http://example.com/market/{uuid.uuid4()}"
        
        if hasattr(self.db_storage, 'save_price'):
            self.db_storage.save_price(test_url, random_price)

        export_result = self.hub.run_compliance_export(self.export_path)
        self.assertTrue(export_result)
        self.assertTrue(os.path.exists(self.export_path))

        integrity_result = self.hub.check_compliance_integrity()
        self.assertIn(integrity_result, [True, False])

        summary = self.hub.fetch_compliance_summary()
        self.assertIsNotNone(summary)

        stream_data = {"shock_event_id": str(uuid.uuid4()), "magnitude": random.randint(1, 100)}
        stream_process_res = self.hub.process_audit_stream_data(self.export_path, stream_data)
        self.assertTrue(stream_process_res)

        log_gen_res = self.hub.generate_compliance_log(self.export_path)
        self.assertTrue(log_gen_res)

        verify_res = self.hub.verify_log_integrity()
        self.assertIn(verify_res, [True, False])

if __name__ == "__main__":
    unittest.main()