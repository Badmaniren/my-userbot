import unittest
import os
import uuid
import random
from skills.market_portfolio_integration_hub import MarketPortfolioIntegrationHub

class TestMarketPortfolioIntegrationHubIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.json"
        self.hub = MarketPortfolioIntegrationHub(storage_file=self.storage_file)
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_url = f"https://example.com/api/{uuid.uuid4()}"
        self.random_shifts = [random.randint(1, 10), random.randint(11, 20)]
        self.telegram_token = f"{random.randint(1000, 9999)}:ABC-{uuid.uuid4().hex[:8]}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_run_integrated_pipeline_real(self):
        result = self.hub.run_integrated_pipeline(
            url=self.random_url,
            symbol=self.random_symbol,
            shifts=self.random_shifts,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )
        self.assertIsInstance(result, bool)

    def test_process_and_export_structure(self):
        pipeline_result = self.hub.process_and_export(
            url=self.random_url,
            symbol=self.random_symbol,
            shifts=self.random_shifts,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )
        self.assertIsInstance(pipeline_result, dict)
        self.assertIn("summary", pipeline_result)
        self.assertIn("export_data", pipeline_result)

    def test_run_full_integration_pipeline_execution(self):
        full_result = self.hub.run_full_integration_pipeline(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            shifts=self.random_shifts
        )
        self.assertIsInstance(full_result, dict)

    def test_execute_custom_export_data(self):
        custom_export = self.hub.execute_custom_export(
            url=self.random_url,
            shifts=self.random_shifts
        )
        self.assertIsNotNone(custom_export)

    def test_export_and_dispatch_stream(self):
        stream_data = self.hub.export_and_dispatch_stream()
        self.assertIsNotNone(stream_data)

if __name__ == "__main__":
    unittest.main()