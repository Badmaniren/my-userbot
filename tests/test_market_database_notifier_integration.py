import unittest
import os
import uuid
import random
from skills.market_database_notifier import MarketDatabaseNotifier

class TestMarketDatabaseNotifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_storage_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"db_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.target_url = f"http://example.com/{uuid.uuid4().hex}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_process_alert_and_persistence_integration(self):
        notifier = MarketDatabaseNotifier(storage_file=self.storage_file, target_url=self.target_url)

        result = notifier.process_alert(symbol=self.symbol, target_url=self.target_url, price=self.price)

        self.assertIsInstance(result, dict)
        self.assertIn(self.symbol, result)
        self.assertEqual(result[self.symbol], self.price)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_check_and_alert_integration(self):
        notifier = MarketDatabaseNotifier(storage_file=self.storage_file, target_url=self.target_url)

        result = notifier.check_and_alert()

        self.assertIsInstance(result, dict)

if __name__ == '__main__':
    unittest.main()