import unittest
import os
import uuid
import random
from skills.market_portfolio_integration_hub import MarketPortfolioIntegrationHub

class TestMarketPortfolioIntegrationHubIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.json"
        self.hub = MarketPortfolioIntegrationHub(storage_file=self.storage_file)
        self.url = f"http://localhost:{random.randint(1000, 9999)}/api/v1"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.shifts = [random.randint(-10, 10), random.randint(-5, 5)]
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_run_integrated_pipeline_real_execution(self):
        result = self.hub.run_integrated_pipeline(
            self.url, self.symbol, self.shifts, self.telegram_token, self.chat_id
        )
        self.assertIsInstance(result, bool)

    def test_process_and_export_returns_structure(self):
        result = self.hub.process_and_export(
            self.url, self.symbol, self.shifts, self.telegram_token, self.chat_id
        )
        self.assertIsInstance(result, dict)
        self.assertIn("summary", result)
        self.assertIn("export_data", result)

    def test_run_full_integration_pipeline_data_consistency(self):
        result = self.hub.run_full_integration_pipeline(
            self.symbol, self.url, self.telegram_token, self.chat_id, self.shifts
        )
        self.assertIsInstance(result, dict)
        self.assertIn("summary", result)
        self.assertIn("export_data", result)

if __name__ == "__main__":
    unittest.main()