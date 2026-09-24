import unittest
import os
import uuid
import random
from skills import market_portfolio_alert_dispatcher

class TestMarketPortfolioAlertDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())[:8]
        self.symbol = f"TICKER_{self.test_id}"
        self.url = f"http://test-endpoint-{self.test_id}.local/api"
        self.telegram_token = f"TOKEN_{random.randint(100000, 999999)}"
        self.chat_id = str(random.randint(10000, 99999))
        self.storage_file = f"test_storage_{self.test_id}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_dispatch_portfolio_alerts_integration(self):
        min_threshold = random.choice(["LOW", "MEDIUM", "HIGH"])
        severity_level = random.choice(["MEDIUM", "HIGH", "CRITICAL"])
        channels = ["telegram"]

        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=severity_level,
            min_threshold=min_threshold,
            channels=channels
        )

        self.assertIsInstance(result, dict)
        if result.get("status") == "filtered_out":
            self.assertIn("status", result)
        else:
            self.assertEqual(result.get("status"), "dispatched")
            self.assertIn("summary", result)
            self.assertIn("pnl", result)
            self.assertTrue(os.path.exists(self.storage_file))

    def test_process_stream_alert_integration(self):
        alert_id = str(uuid.uuid4())
        stream_data = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
        self.assertIsNotNone(stream_data)

if __name__ == "__main__":
    unittest.main()