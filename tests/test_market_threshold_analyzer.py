import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.market_threshold_analyzer import analyze_and_notify, analyze_and_check_thresholds

class TestMarketThresholdAnalyzer(unittest.TestCase):

    def setUp(self):
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/market"
        self.token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"{uuid.uuid4().hex}.json"

    def test_analyze_and_notify_exceeded(self):
        random_price = round(random.uniform(150.0, 300.0), 2)
        random_threshold = random_price - 50.0

        with patch('skills.market_threshold_analyzer.MarketParser') as MockParserClass, \
             patch('skills.market_threshold_analyzer.send_telegram_notification') as mock_send_notif:

            mock_parser_instance = MockParserClass.return_value
            mock_parser_instance.fetch_price.return_value = random_price

            result = analyze_and_notify(
                self.symbol,
                self.url,
                random_threshold,
                self.token,
                self.chat_id,
                self.storage_file
            )

            self.assertTrue(result)
            MockParserClass.assert_called_once_with(storage_file=self.storage_file)
            mock_parser_instance.fetch_price.assert_called_once_with(self.url)
            mock_parser_instance.fetch_and_store.assert_called_once_with(self.symbol, random_price)

            mock_send_notif.assert_called_once()
            args, _ = mock_send_notif.call_args
            self.assertEqual(args[0], self.token)
            self.assertEqual(args[1], self.chat_id)
            self.assertIn(self.symbol, args[2])
            self.assertIn(str(random_price), args[2])

    def test_analyze_and_notify_not_exceeded(self):
        random_price = round(random.uniform(50.0, 100.0), 2)
        random_threshold = random_price + 50.0

        with patch('skills.market_threshold_analyzer.MarketParser') as MockParserClass, \
             patch('skills.market_threshold_analyzer.send_telegram_notification') as mock_send_notif:

            mock_parser_instance = MockParserClass.return_value
            mock_parser_instance.fetch_price.return_value = random_price

            result = analyze_and_notify(
                self.symbol,
                self.url,
                random_threshold,
                self.token,
                self.chat_id,
                self.storage_file
            )

            self.assertFalse(result)
            MockParserClass.assert_called_once_with(storage_file=self.storage_file)
            mock_parser_instance.fetch_price.assert_called_once_with(self.url)
            mock_parser_instance.fetch_and_store.assert_called_once_with(self.symbol, random_price)
            mock_send_notif.assert_not_called()

    def test_analyze_and_check_thresholds_list_prices(self):
        p1 = round(random.uniform(10.0, 50.0), 2)
        p2 = round(random.uniform(51.0, 100.0), 2)
        fake_prices = [p1, p2]
        threshold = p2 - 10.0

        with patch('skills.market_threshold_analyzer.load_data') as mock_load_data:
            mock_load_data.return_value = {self.symbol: fake_prices}

            res = analyze_and_check_thresholds(self.storage_file, self.symbol, threshold)

            mock_load_data.assert_called_once_with(self.storage_file)
            self.assertTrue(res["exceeded"])
            self.assertEqual(res["current_price"], p2)

    def test_analyze_and_check_thresholds_single_numeric_price(self):
        single_price = round(random.uniform(100.0, 200.0), 2)
        threshold = single_price + 10.0

        with patch('skills.market_threshold_analyzer.load_data') as mock_load_data:
            mock_load_data.return_value = {self.symbol: single_price}

            res = analyze_and_check_thresholds(self.storage_file, self.symbol, threshold)

            mock_load_data.assert_called_once_with(self.storage_file)
            self.assertFalse(res["exceeded"])
            self.assertEqual(res["current_price"], single_price)

    def test_analyze_and_check_thresholds_empty_or_invalid_data(self):
        threshold = round(random.uniform(1.0, 10.0), 2)

        with patch('skills.market_threshold_analyzer.load_data') as mock_load_data:
            mock_load_data.return_value = {self.symbol: "invalid_type_data"}

            res = analyze_and_check_thresholds(self.storage_file, self.symbol, threshold)

            mock_load_data.assert_called_once_with(self.storage_file)
            self.assertFalse(res["exceeded"])
            self.assertEqual(res["current_price"], 0.0)

if __name__ == '__main__':
    unittest.main()