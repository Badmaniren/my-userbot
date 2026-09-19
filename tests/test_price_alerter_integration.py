import os
import tempfile
import unittest
import uuid
import random
from skills.price_alerter import MarketParser, PriceAlerter


class TestPriceAlerterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage_file = os.path.join(self.test_dir, f"market_{uuid.uuid4().hex}.json")
        self.parser = MarketParser(storage_file=self.storage_file)
        self.alerter = PriceAlerter(parser=self.parser)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_price_alert_triggered_on_threshold_exceeded(self):
        random_token = uuid.uuid4().hex[:6].upper()
        symbol = f"CRYPTO_{random_token}"
        initial_price = round(random.uniform(100.0, 1000.0), 2)

        self.parser.fetch_and_store(symbol, initial_price)
        self.assertTrue(os.path.exists(self.storage_file))

        threshold_percent = 10.0
        price_multiplier = 1.0 + (threshold_percent + random.uniform(2.0, 10.0)) / 100.0
        new_price = round(initial_price * price_multiplier, 2)
        expected_change_pct = round(((new_price - initial_price) / initial_price) * 100.0, 2)

        result = self.alerter.check_threshold(symbol, new_price, threshold_percent)

        self.assertIsNotNone(result)
        self.assertTrue(result.get("triggered"))
        self.assertEqual(result.get("symbol"), symbol)
        self.assertEqual(result.get("old_price"), initial_price)
        self.assertEqual(result.get("new_price"), new_price)
        self.assertAlmostEqual(result.get("change_percent"), expected_change_pct, places=1)

        message = result.get("message", "")
        self.assertIn(symbol, message)
        self.assertIn(str(new_price), message)

    def test_price_alert_not_triggered_below_threshold(self):
        random_token = uuid.uuid4().hex[:6].upper()
        symbol = f"CRYPTO_{random_token}"
        initial_price = round(random.uniform(500.0, 2000.0), 2)

        self.parser.fetch_and_store(symbol, initial_price)

        threshold_percent = 10.0
        new_price = round(initial_price * 1.01, 2)

        result = self.alerter.check_threshold(symbol, new_price, threshold_percent)

        self.assertIsNotNone(result)
        self.assertFalse(result.get("triggered"))
        self.assertEqual(result.get("symbol"), symbol)
        self.assertEqual(result.get("old_price"), initial_price)
        self.assertEqual(result.get("new_price"), new_price)

    def test_format_notification_contains_dynamic_data(self):
        random_token = uuid.uuid4().hex[:6].upper()
        symbol = f"CRYPTO_{random_token}"
        old_price = round(random.uniform(50.0, 200.0), 2)
        new_price = round(old_price * 1.25, 2)
        change_percent = 25.0

        formatted = self.alerter.format_notification(symbol, old_price, new_price, change_percent)
        self.assertIsInstance(formatted, str)
        self.assertIn(symbol, formatted)
        self.assertIn(str(old_price), formatted)
        self.assertIn(str(new_price), formatted)


if __name__ == "__main__":
    unittest.main()