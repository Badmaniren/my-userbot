import unittest
import os
import uuid
import random
from skills import market_portfolio_alert_dispatcher

class TestMarketPortfolioAlertDispatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.symbol = f"TEST_{self.random_suffix}"
        self.url = f"http://localhost:8080/api/v1/test_{self.random_suffix}"
        self.telegram_token = f"token_{self.random_suffix}"
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_storage_{self.random_suffix}.json"
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.min_threshold = "LOW"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_dispatch_portfolio_alerts_integration(self):
        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=["telegram"]
        )

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "dispatched")
        self.assertIn("summary", result)
        self.assertIn("pnl", result)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_dispatch_portfolio_alerts_filtered_out(self):
        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level="LOW",
            min_threshold="CRITICAL",
            channels=["telegram"]
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "filtered_out")

    def test_process_stream_alert_integration(self):
        alert_id = f"alert_{self.random_suffix}"
        stream_obj = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
        self.assertIsNotNone(stream_obj)
        self.assertTrue(hasattr(stream_obj, "read"))

if __name__ == "__main__":
    unittest.main()