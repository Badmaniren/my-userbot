import unittest
import os
import uuid
import random
from skills.market_notifier import MarketNotifier
from skills import market_parser
from skills import db_storage

class TestMarketNotifierIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_id = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_storage_{self.unique_id}.json"
        self.notifier = MarketNotifier(storage_file=self.storage_file)
        self.test_symbol = f"SYM_{self.unique_id}"
        self.test_url = f"http://example.com/price/{self.unique_id}"
        self.random_price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_integration_check_and_notify_real_flow(self):
        threshold = self.random_price - 5.0

        if hasattr(self.notifier.parser, "fetch_price"):
            original_fetch = self.notifier.parser.fetch_price
            self.notifier.parser.fetch_price = lambda url: self.random_price
        else:
            market_parser.fetch_price = lambda url: self.random_price

        try:
            result = self.notifier.check_and_notify(self.test_symbol, self.test_url, threshold)

            self.assertEqual(result["symbol"], self.test_symbol)
            self.assertEqual(result["price"], self.random_price)
            self.assertTrue(result["alert_triggered"])

            history = self.notifier.load_history()
            self.assertIn(self.test_symbol, history)
            self.assertEqual(history[self.test_symbol], self.random_price)

            alert_msg = self.notifier.send_alert(self.test_symbol, self.random_price, threshold)
            self.assertIn(self.test_symbol, alert_msg)
            self.assertIn(str(self.random_price), alert_msg)

        finally:
            if hasattr(self.notifier.parser, "fetch_price"):
                self.notifier.parser.fetch_price = original_fetch

    def test_integration_process_and_notify_storage_persistence(self):
        target_price = self.random_price + 10.0

        if hasattr(self.notifier.parser, "fetch_price"):
            original_fetch = self.notifier.parser.fetch_price
            self.notifier.parser.fetch_price = lambda url: self.random_price
        else:
            market_parser.fetch_price = lambda url: self.random_price

        try:
            result = self.notifier.process_and_notify(self.test_symbol, self.test_url, target_price)

            self.assertEqual(result["symbol"], self.test_symbol)
            self.assertEqual(result["price"], self.random_price)
            self.assertFalse(result["alert_triggered"])

            self.assertTrue(os.path.exists(self.storage_file))

            history = self.notifier.load_history()
            self.assertEqual(history.get(self.test_symbol), self.random_price)

        finally:
            if hasattr(self.notifier.parser, "fetch_price"):
                self.notifier.parser.fetch_price = original_fetch

if __name__ == "__main__":
    unittest.main()