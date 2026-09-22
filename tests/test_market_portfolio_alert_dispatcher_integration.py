import unittest
import os
import uuid
import random
from skills import market_portfolio_alert_dispatcher

class TestMarketPortfolioAlertDispatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.random_uuid = str(uuid.uuid4())
        self.storage_file = f"test_storage_{self.random_uuid}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.chat_id = str(random.randint(100000, 999999))
        self.telegram_token = f"token_{random.randint(100, 999)}:ABC"
        self.test_url = f"http://localhost:{random.randint(8000, 9999)}/market"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
        storage_dir = os.path.dirname(os.path.abspath(self.storage_file))
        if storage_dir and os.path.exists(storage_dir) and not os.listdir(storage_dir):
            try:
                os.rmdir(storage_dir)
            except OSError:
                pass

    def test_dispatch_portfolio_alerts_integration(self):
        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            self.symbol,
            self.test_url,
            self.telegram_token,
            self.chat_id,
            self.storage_file
        )

        self.assertIsInstance(result, dict)
        self.assertIn("summary", result)
        self.assertIn("pnl", result)
        self.assertEqual(result.get("status"), "dispatched")

        self.assertTrue(
            os.path.exists(self.storage_file),
            "Файл хранилища должен быть создан в результате работы интеграционного пайплайна"
        )

    def test_process_stream_alert_integration(self):
        stream_data = market_portfolio_alert_dispatcher.process_stream_alert(self.random_uuid)
        self.assertIsNotNone(stream_data)

if __name__ == "__main__":
    unittest.main()