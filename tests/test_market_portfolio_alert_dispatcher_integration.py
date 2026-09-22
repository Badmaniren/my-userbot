import unittest
import os
import uuid
import random
from skills import market_portfolio_alert_dispatcher

class TestMarketPortfolioAlertDispatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"http://example.com/api/{uuid.uuid4().hex[:8]}"
        self.telegram_token = f"TOKEN_{uuid.uuid4().hex[:8]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_dispatch_portfolio_alerts_integration(self):
        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            self.symbol, 
            self.url, 
            self.telegram_token, 
            self.chat_id, 
            self.storage_file
        )

        self.assertIsInstance(result, dict)
        self.assertIn("summary", result)
        self.assertIn("pnl", result)
        self.assertEqual(result.get("status"), "dispatched")
        
        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be created during integration pipeline execution.")

    def test_process_stream_alert_integration(self):
        alert_id = f"ALERT_{uuid.uuid4().hex[:8]}"
        stream_data = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
        
        self.assertIsNotNone(stream_data)

if __name__ == "__main__":
    unittest.main()