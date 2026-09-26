import unittest
import os
import uuid
import random
import io
from skills import market_portfolio_alert_dispatcher
from skills import market_portfolio_monitor
from skills import market_portfolio_valuation

class TestMarketPortfolioAlertDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())
        self.symbol = f"TICKER_{random.randint(1000, 9999)}_{self.test_id[:6]}"
        self.url = f"https://api.internal-market-monitor.net/v1/data/{self.test_id}"
        self.telegram_token = f"bot_token_{random.randint(100000, 999999)}"
        self.chat_id = f"chat_{random.randint(10000, 99999)}"
        self.storage_file = f"test_storage_{self.test_id}.json"
        self.alert_id = f"alert_stream_{random.randint(100, 999)}_{self.test_id[:4]}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_dispatch_portfolio_alerts_integration(self):
        min_threshold_options = [None, "LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_threshold = random.choice(min_threshold_options)

        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severity_levels)

        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=chosen_severity,
            min_threshold=chosen_threshold,
            channels=["telegram"]
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
        stream_result = market_portfolio_alert_dispatcher.process_stream_alert(self.alert_id)
        self.assertTrue(
            isinstance(stream_result, io.IOBase) or hasattr(stream_result, "read"),
            "Result should be a file-like stream object"
        )

if __name__ == "__main__":
    unittest.main()