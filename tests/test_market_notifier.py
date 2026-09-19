import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.market_notifier import MarketNotifier

class TestMarketNotifier(unittest.TestCase):
    def setUp(self):
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/market"
        self.threshold = round(random.uniform(50.0, 150.0), 2)

        self.mock_parser = MagicMock()
        self.mock_storage = MagicMock()

        self.notifier = MarketNotifier(
            parser=self.mock_parser,
            storage=self.mock_storage,
            threshold=self.threshold
        )

    def test_check_and_alert_above_threshold(self):
        high_price = self.threshold + round(random.uniform(1.0, 50.0), 2)
        self.mock_parser.fetch_price.return_value = high_price

        result = self.notifier.check_and_alert(self.symbol, self.url)

        self.mock_parser.fetch_price.assert_called_once_with(self.url)
        self.mock_parser.fetch_and_store.assert_called_once_with(self.symbol, high_price)
        self.assertIn("ALERT", result)
        self.assertIn(self.symbol, result)
        self.assertIn(str(high_price), result)

    def test_check_and_alert_normal_below_threshold(self):
        low_price = max(0.1, self.threshold - round(random.uniform(1.0, 50.0), 2))
        self.mock_parser.fetch_price.return_value = low_price

        result = self.notifier.check_and_alert(self.symbol, self.url)

        self.mock_parser.fetch_price.assert_called_once_with(self.url)
        self.mock_parser.fetch_and_store.assert_called_once_with(self.symbol, low_price)
        self.assertIn("NORMAL", result)
        self.assertIn(self.symbol, result)
        self.assertIn(str(low_price), result)

    def test_evaluate_market_filters_correctly(self):
        sym_high = ''.join(random.choices(string.ascii_uppercase, k=4))
        sym_low = ''.join(random.choices(string.ascii_uppercase, k=4))
        price_high = self.threshold + 10.0
        price_low = self.threshold - 10.0

        market_data = {
            sym_high: price_high,
            sym_low: price_low
        }
        self.mock_parser.parse_html_prices.return_value = market_data

        alerts = self.notifier.evaluate_market(self.url)

        self.mock_parser.parse_html_prices.assert_called_once_with(self.url)
        self.assertIn((sym_high, price_high), alerts)
        self.assertNotIn((sym_low, price_low), alerts)

    def test_check_and_notify_true(self):
        price = self.threshold + round(random.uniform(0.1, 10.0), 2)

        result = self.notifier.check_and_notify(self.symbol, price)

        self.mock_parser.fetch_and_store.assert_called_once_with(self.symbol, price)
        self.assertTrue(result)

    def test_check_and_notify_false(self):
        price = max(0.0, self.threshold - round(random.uniform(0.1, 10.0), 2))

        result = self.notifier.check_and_notify(self.symbol, price)

        self.mock_parser.fetch_and_store.assert_called_once_with(self.symbol, price)
        self.assertFalse(result)

    def test_default_initialization_instantiation(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        with patch('skills.market_notifier.MarketParser') as mock_parser_cls, \
             patch('skills.market_notifier.DBStorage') as mock_storage_cls:

            notifier = MarketNotifier(storage_file=storage_file, threshold=self.threshold)

            mock_parser_cls.assert_called_once_with(storage_file=storage_file)
            mock_storage_cls.assert_called_once()
            self.assertEqual(notifier.threshold, self.threshold)