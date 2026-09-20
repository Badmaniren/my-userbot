import unittest
import os
import uuid
import random
from unittest.mock import patch
from skills.market_threshold_analyzer import analyze_and_notify, analyze_and_check_thresholds

class TestMarketThresholdAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_market_data_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_price = round(random.uniform(10.0, 1000.0), 2)
        self.threshold = self.random_price - 5.0  # Гарантируем превышение для теста
        self.url = f"https://example.com/market/{uuid.uuid4()}"
        self.telegram_token = f"fake_token_{uuid.uuid4()}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    @patch('skills.market_threshold_analyzer.MarketParser.fetch_price')
    @patch('skills.market_threshold_analyzer.send_telegram_notification')
    def operation_flow_test(self, mock_send_telegram, mock_fetch_price):
        mock_fetch_price.return_value = self.random_price

        exceeded = analyze_and_notify(
            symbol=self.symbol,
            url=self.url,
            threshold=self.threshold,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(exceeded)
        mock_fetch_price.assert_called_once_with(self.url)
        mock_send_telegram.assert_called_once()

        call_args = mock_send_telegram.call_args[0]
        self.assertEqual(call_args[0], self.telegram_token)
        self.assertEqual(call_args[1], self.chat_id)
        self.assertIn(self.symbol, call_args[2])
        self.assertIn(str(self.random_price), call_args[2])

        self.assertTrue(os.path.exists(self.storage_file))

        result_check = analyze_and_check_thresholds(
            storage_file=self.storage_file,
            symbol=self.symbol,
            threshold=self.threshold
        )

        self.assertIsInstance(result_check, dict)
        self.assertTrue(result_check["exceeded"])
        self.assertEqual(result_check["current_price"], self.random_price)

    def test_integration_pipeline_execution(self):
        self.operation_flow_test()

if __name__ == '__main__':
    unittest.main()