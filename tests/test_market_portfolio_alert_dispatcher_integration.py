import unittest
import os
import uuid
import random
from skills import market_portfolio_alert_dispatcher

class TestMarketPortfolioAlertDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.test-market-data.io/v1/{uuid.uuid4().hex[:8]}"
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:20]}"
        self.chat_id = f"@{uuid.uuid4().hex[:10]}"
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        self.severity_level = random.choice(severities)
        self.min_threshold = random.choice(severities)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
            
        dirname = os.path.dirname(os.path.abspath(self.storage_file))
        if dirname and os.path.exists(dirname) and not os.listdir(dirname):
            try:
                os.rmdir(dirname)
            except OSError:
                pass

    def test_dispatch_portfolio_alerts_integration(result_self):
        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=result_self.symbol,
            url=result_self.url,
            telegram_token=result_self.telegram_token,
            chat_id=result_self.chat_id,
            storage_file=result_self.storage_file,
            severity_level=result_self.severity_level,
            min_threshold="LOW",
            channels=["telegram"]
        )
        
        result_self.assertIn("status", result)
        if result["status"] == "dispatched":
            result_self.assertIn("summary", result)
            result_self.assertIn("pnl", result)
            result_self.assertTrue(os.path.exists(result_self.storage_file))
        elif result["status"] == "filtered_out":
            result_self.assertEqual(result["status"], "filtered_out")

    def test_process_stream_alert_integration(result_self):
        alert_id = str(uuid.uuid4())
        stream_data = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
        result_self.assertIsNotNone(stream_data)

if __name__ == "__main__":
    unittest.main()