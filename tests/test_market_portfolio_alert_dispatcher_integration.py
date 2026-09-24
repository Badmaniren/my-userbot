import unittest
import os
import uuid
import tempfile
from skills import market_portfolio_alert_dispatcher
from skills import db_storage

class TestMarketPortfolioAlertDispatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"storage_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"http://127.0.0.1:8000/api/{uuid.uuid4().hex}"
        self.telegram_token = f"tok_{uuid.uuid4().hex}"
        self.chat_id = str(uuid.uuid4().int)[:8]

    def tearDown(self):
        self.test_dir.cleanup()

    def test_dispatch_portfolio_alerts_integration_flow(self):
        min_threshold = "LOW"
        severity_level = "HIGH"
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
        self.assertEqual(result.get("status"), "dispatched")
        self.assertIn("summary", result)
        self.assertIn("pnl", result)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_dispatch_portfolio_alerts_filtering(self):
        min_threshold = "CRITICAL"
        severity_level = "LOW"

        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=severity_level,
            min_threshold=min_threshold,
            channels=["telegram"]
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "filtered_out")

    def test_process_stream_alert_integration(self):
        random_alert_id = str(uuid.uuid4())
        stream_data = market_portfolio_alert_dispatcher.process_stream_alert(random_alert_id)
        self.assertTrue(hasattr(stream_data, "read"))

if __name__ == "__main__":
    unittest.main()
