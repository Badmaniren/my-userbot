import unittest
import os
import uuid
import random
from skills import market_portfolio_alert_dispatcher

class TestMarketPortfolioAlertDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())
        self.symbol = f"TICKER_{random.randint(1000, 9999)}"
        self.url = f"http://example.com/api/{self.test_id}"
        self.telegram_token = f"token_{random.randint(10000, 99999)}"
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_storage_{self.test_id}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_dispatch_portfolio_alerts_integration(self):
        min_threshold_val = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        severity_val = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=severity_val,
            min_threshold=min_threshold_val,
            channels=["telegram"]
        )

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        
        if result["status"] == "dispatched":
            self.assertIn("summary", result)
            self.assertIn("pnl", result)
            self.assertTrue(os.path.exists(self.storage_file))
        elif result["status"] == "filtered_out":
            pass
        else:
            self.fail(f"Unexpected status returned: {result['status']}")

    def test_process_stream_alert_integration(self):
        stream_alert_id = f"alert_{uuid.uuid4()}"
        stream_result = market_portfolio_alert_dispatcher.process_stream_alert(stream_alert_id)
        self.assertIsNotNone(stream_result)

if __name__ == "__main__":
    unittest.main()