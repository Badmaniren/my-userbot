import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
from skills.market_notifier import MarketNotifier

class TestMarketNotifierComposition(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        self.url = f"https://example.com/market/{uuid.uuid4().hex[:6]}"
        self.threshold = random.uniform(10.0, 100.0)
        self.price = self.threshold + random.uniform(1.0, 50.0)
        self.notifier = MarketNotifier(storage_file=self.storage_file)

    def test_init_sets_storage_file(self):
        random_file = f"{uuid.uuid4().hex}.json"
        notifier = MarketNotifier(storage_file=random_file)
        self.assertEqual(notifier.storage_file, random_file)

    def test_send_alert_format(self):
        symbol = f"SYM_{uuid.uuid4().hex[:4]}"
        price = random.uniform(100.0, 500.0)
        threshold = random.uniform(50.0, 99.0)
        result = self.notifier.send_alert(symbol, price, threshold)
        self.assertIn(symbol, result)
        self.assertIn(str(price), result)
        self.assertIn(str(threshold), result)
        self.assertTrue(result.startswith("ALERT:"))

    def test_check_and_notify_triggers_alert_when_threshold_exceeded(self):
        with patch.object(self.notifier.parser, "fetch_price", return_value=self.price), \
             patch.object(self.notifier.storage, "fetch_and_store", create=True) as mock_store:

            result = self.notifier.check_and_notify(self.symbol, self.url, self.threshold)

            self.assertEqual(result["symbol"], self.symbol)
            self.assertEqual(result["price"], self.price)
            self.assertTrue(result["alert_triggered"])
            mock_store.assert_called_once_with(self.symbol, self.price)

    def test_check_and_notify_no_alert_when_below_threshold(self):
        low_price = self.threshold - random.uniform(1.0, 5.0)
        with patch.object(self.notifier.parser, "fetch_price", return_value=low_price), \
             patch.object(self.notifier.storage, "fetch_and_store", create=True) as mock_store:

            result = self.notifier.check_and_notify(self.symbol, self.url, self.threshold)

            self.assertEqual(result["symbol"], self.symbol)
            self.assertEqual(result["price"], low_price)
            self.assertFalse(result["alert_triggered"])
            mock_store.assert_called_once_with(self.symbol, low_price)

    def test_load_history_uses_load_data(self):
        expected_data = {f"SYM_{uuid.uuid4().hex[:4]}": random.uniform(1.0, 100.0)}
        with patch.object(self.notifier.storage, "load_data", return_value=expected_data, create=True):
            data = self.notifier.load_history()
            self.assertEqual(data, expected_data)

    def test_load_history_fallback_empty(self):
        mock_storage = MagicMock(spec=[])
        with patch.object(self.notifier, "storage", mock_storage):
            data = self.notifier.load_history()
            self.assertEqual(data, {})

    def test_process_and_notify_triggers_alert(self):
        initial_data = {f"SYM_{uuid.uuid4().hex[:4]}": random.uniform(10.0, 50.0)}
        with patch.object(self.notifier.parser, "fetch_price", return_value=self.price), \
             patch("skills.market_notifier.hasattr", return_value=True), \
             patch.object(self.notifier.storage, "load_market_data", return_value=initial_data, create=True), \
             patch.object(self.notifier.storage, "save_market_data", create=True) as mock_save:

            result = self.notifier.process_and_notify(self.symbol, self.url, self.threshold)

            self.assertEqual(result["symbol"], self.symbol)
            self.assertEqual(result["price"], self.price)
            self.assertTrue(result["alert_triggered"])
            mock_save.assert_called_once()
            saved_args = mock_save.call_args[0]
            self.assertEqual(saved_args[0], self.storage_file)
            self.assertEqual(saved_args[1][self.symbol], self.price)