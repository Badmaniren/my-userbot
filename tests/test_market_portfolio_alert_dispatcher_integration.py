import unittest
import os
import uuid
import tempfile
from skills import market_portfolio_alert_dispatcher

class TestMarketPortfolioAlertDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"http://127.0.0.1:8000/{uuid.uuid4().hex[:6]}"
        self.telegram_token = f"token_{uuid.uuid4().hex[:8]}"
        self.chat_id = str(uuid.uuid4().int)[:6]

        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"storage_{uuid.uuid4().hex[:8]}.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dispatch_portfolio_alerts_integration(self):
        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertIsInstance(result, dict)
        self.assertIn("summary", result)
        self.assertIn("pnl", result)
        self.assertEqual(result.get("status"), "dispatched")

        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища должен быть создан в ходе выполнения пайплайна")

    def test_process_stream_alert_integration(self):
        alert_id = uuid.uuid4().hex
        stream_data = market_portfolio_alert_dispatcher.process_stream_alert(alert_id=alert_id)

        self.assertIsNotNone(stream_data)
        if hasattr(stream_data, "read"):
            content = stream_data.read()
            self.assertIsInstance(content, bytes)

if __name__ == "__main__":
    unittest.main()