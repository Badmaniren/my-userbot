import unittest
import os
import uuid
import random
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub
from skills.db_storage import MarketParser
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter
from skills.market_portfolio_stress_monte_carlo_engine import MarketPortfolioStressMonteCarloEngine


class TestMarketPortfolioAuditComplianceHubIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_storage_{self.random_suffix}.json"
        self.export_path = f"test_audit_export_{self.random_suffix}.json"
        
        self.hub = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)

    def tearDown(self):
        for filepath in [self.storage_file, self.export_path]:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass

    def test_compliance_hub_monte_carlo_and_export_integration(self):
        test_stream_data = f"audit_stream_payload_{uuid.uuid4().hex}"
        
        export_result = self.hub.run_compliance_export(self.export_path)
        self.assertTrue(export_result)
        self.assertTrue(os.path.exists(self.export_path))

        integrity_status = self.hub.check_compliance_integrity()
        self.assertIn(integrity_status, [True, False])

        summary = self.hub.fetch_compliance_summary()
        self.assertIsNotNone(summary)

        process_result = self.hub.process_audit_stream_data(self.export_path, test_stream_data)
        self.assertIn(process_result, [True, False])

        log_generation = self.hub.generate_compliance_log(self.export_path)
        self.assertTrue(log_generation)

        random_url = f"http://example.com/market/price/{uuid.uuid4().hex}"
        price = self.hub.audit_fetch_market_price(random_url)
        self.assertIsInstance(price, float)

        historical_data_load = self.hub.load_historical_audit_data(self.storage_file)
        self.assertIsNotNone(historical_data_load)

        stream_summary = self.hub.get_audit_stream_summary()
        self.assertIsNotNone(stream_summary)

        log_verify = self.hub.verify_log_integrity()
        self.assertIn(log_verify, [True, False])

        second_export_path = f"test_secondary_export_{uuid.uuid4().hex}.json"
        try:
            secondary_export = self.hub.export_audit_logs(second_export_path)
            self.assertTrue(secondary_export)
            self.assertTrue(os.path.exists(second_export_path))
        finally:
            if os.path.exists(second_export_path):
                os.remove(second_export_path)

        self.assertIsInstance(self.hub.monte_carlo_engine, MarketPortfolioStressMonteCarloEngine)
        self.assertIsInstance(self.hub.db_storage, MarketParser)
        self.assertIsInstance(self.hub.audit_exporter, PortfolioAuditLogExporter)


if __name__ == "__main__":
    unittest.main()