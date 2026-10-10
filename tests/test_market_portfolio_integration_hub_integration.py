import unittest
import os
import uuid
import random
from skills.market_portfolio_integration_hub import MarketPortfolioIntegrationHub

class TestMarketPortfolioIntegrationHubReal(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.hub = MarketPortfolioIntegrationHub(storage_file=self.storage_file)
        self.test_url = f"https://api.test-portfolio-{uuid.uuid4().hex[:8]}.local/v1"
        self.test_symbol = f"TICKER_{random.randint(1000, 9999)}"
        self.test_shifts = [random.randint(-10, 10), random.randint(-20, 20)]
        self.telegram_token = f"bot{random.randint(100000, 999999)}:ABC{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(1000000, 99999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_integration_pipeline_execution(self):
        result = self.hub.run_integrated_pipeline(
            url=self.test_url,
            symbol=self.test_symbol,
            shifts=self.test_shifts,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )
        self.assertIsInstance(result, bool)

    def test_full_integration_pipeline_payload(self):
        pipeline_output = self.hub.run_full_integration_pipeline(
            symbol=self.test_symbol,
            url=self.test_url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            shifts=self.test_shifts
        )
        self.assertIsInstance(pipeline_output, dict)
        self.assertIn("summary", pipeline_output)
        self.assertIn("export_data", pipeline_output)

    def test_custom_export_and_stream(self):
        custom_export_result = self.hub.execute_custom_export(self.test_url, self.test_shifts)
        stream_result = self.hub.export_and_dispatch_stream()
        self.assertIsNotNone(custom_export_result)
        self.assertIsNotNone(stream_result)

if __name__ == "__main__":
    unittest.main()