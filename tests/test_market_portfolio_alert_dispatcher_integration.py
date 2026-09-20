import unittest
import os
import uuid
import tempfile
from skills import market_portfolio_alert_dispatcher

class TestMarketPortfolioAlertDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"portfolio_store_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"http://127.0.0.1:8000/market/{uuid.uuid4().hex}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(uuid.uuid4().int)[:8]

    def tearDown(self):
        self.test_dir.cleanup()

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
        self.assertTrue(os.path.exists(self.storage_file))

    def test_process_stream_alert_integration(self):
        alert_id = uuid.uuid4().hex
        stream_data = market_portfolio_alert_dispatcher.process_stream_alert(alert_id)
        self.assertIsNotNone(stream_data)
        content = stream_data.read()
        self.assertIsInstance(content, bytes)

if __name__ == '__main__':
    unittest.main()