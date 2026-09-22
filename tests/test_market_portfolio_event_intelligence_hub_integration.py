import unittest
import os
import uuid
import random
from skills.market_portfolio_event_intelligence_hub import (
    process_intelligence_hub_trigger,
    MarketPortfolioEventIntelligenceHub
)

class TestMarketPortfolioEventIntelligenceHubIntegration(unittest.TestCase):
    
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{random.randint(100, 999)}"
        self.url = f"https://api.test.v1/webhook/{uuid.uuid4()}"
        self.token = f"token_{uuid.uuid4()}"
        self.chat_id = str(random.randint(100000, 999999))
        self.severity = random.choice(["INFO", "WARNING", "CRITICAL"])
        self.threshold = round(random.uniform(1.0, 100.0), 2)
        self.channels = ["telegram", "webhook"]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_intelligence_hub_integration_flow(self):
        result = process_intelligence_hub_trigger(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=self.severity,
            min_threshold=self.threshold,
            channels=self.channels
        )

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "success")
        self.assertIn("processed_symbol", result)
        self.assertEqual(result["processed_symbol"], self.symbol)

        hub_instance = MarketPortfolioEventIntelligenceHub(storage_file=self.storage_file)
        analytics_report = hub_instance.evaluate_and_process_intelligence(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.token,
            chat_id=self.chat_id,
            severity_level=self.severity,
            min_threshold=self.threshold,
            channels=self.channels
        )

        self.assertIsInstance(analytics_report, dict)
        self.assertIn("analytics_metric", analytics_report)
        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be created by integrated sinks and routers.")

if __name__ == "__main__":
    unittest.main()