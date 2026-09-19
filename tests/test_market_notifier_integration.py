import unittest
import os
import uuid
import tempfile
from skills.market_notifier import MarketNotifier

class TestMarketNotifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_db_{uuid.uuid4().hex}.json")
        self.notifier = MarketNotifier(threshold=150.0, storage_file=self.storage_file)
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_url = f"http://example.com/market/{uuid.uuid4().hex}"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_check_and_alert_integration(self):
        high_price = 175.5

        class DummyParser:
            def __init__(self, storage_file=None):
                pass
            def fetch_price(self, url):
                return high_price
            def fetch_and_store(self, symbol, price):
                pass

        notifier = MarketNotifier(parser=DummyParser(), threshold=150.0, storage_file=self.storage_file)
        result = notifier.check_and_alert(self.random_symbol, self.random_url)

        self.assertIn("ALERT", result)
        self.assertIn(self.random_symbol, result)
        self.assertIn(str(high_price), result)

    def test_evaluate_market_integration(self):
        target_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        low_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

        class DummyParserBatch:
            def __init__(self, storage_file=None):
                pass
            def parse_html_prices(self, url):
                return {
                    target_symbol: 200.0,
                    low_symbol: 50.0
                }

        notifier = MarketNotifier(parser=DummyParserBatch(), threshold=150.0, storage_file=self.storage_file)
        alerts = notifier.evaluate_market(self.random_url)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0][0], target_symbol)
        self.assertEqual(alerts[0][1], 200.0)

    def test_check_and_notify_real_storage(self):
        price = 120.0
        result = self.notifier.check_and_notify(self.random_symbol, price)

        self.assertFalse(result)
        self.assertTrue(os.path.exists(self.storage_file))

if __name__ == '__main__':
    unittest.main()