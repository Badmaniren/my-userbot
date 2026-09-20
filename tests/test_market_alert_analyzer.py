import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
from skills.market_alert_analyzer import MarketAlertAnalyzer

class TestMarketAlertAnalyzer(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.url = f"https://{uuid.uuid4().hex}.com/price"
        self.threshold = random.uniform(10.0, 1000.0)
        self.analyzer = MarketAlertAnalyzer(self.storage_file)

    def test_analyze_and_trigger_alert_success(self):
        random_price = random.uniform(1.0, 5000.0)
        random_id = uuid.uuid4().hex

        with patch('skills.market_parser.MarketParser') as MockParser:
            with patch('skills.db_storage.MarketParser') as MockStorage:
                mock_parser_instance = MockParser.return_value
                mock_parser_instance.fetch_price.return_value = random_price

                mock_storage_instance = MockStorage.return_value
                mock_storage_instance.load_data.return_value = {self.symbol: self.threshold}

                result = self.analyzer.check_threshold(self.symbol, self.url)

                self.assertEqual(result, random_price > self.threshold)
                mock_parser_instance.fetch_price.assert_called_once_with(self.url)

    def test_trigger_notification_flow(self):
        random_token = uuid.uuid4().hex
        random_chat_id = str(random.randint(100000, 999999))
        random_msg = uuid.uuid4().hex

        with patch('skills.market_telegram_pipeline.send_telegram_notification') as mock_send:
            self.analyzer.send_alert(random_token, random_chat_id, random_msg)

            mock_send.assert_called_once_with(random_token, random_chat_id, random_msg)

    def test_data_integrity_with_random_payload(self):
        random_data = {
            'symbol': ''.join(random.choices(string.ascii_uppercase, k=3)),
            'price': random.random() * 100
        }

        with patch('skills.db_storage.MarketParser') as MockStorage:
            mock_storage_instance = MockStorage.return_value
            mock_storage_instance.fetch_and_store.return_value = True

            status = self.analyzer.update_market_data(random_data['symbol'], random_data['price'])

            self.assertTrue(status)
            mock_storage_instance.fetch_and_store.assert_called_with(
                random_data['symbol'],
                random_data['price']
            )

    def test_parser_html_handling_with_random_bytes(self):
        random_bytes = uuid.uuid4().hex.encode('utf-8')

        with patch('skills.market_parser.MarketParser') as MockParser:
            mock_parser_instance = MockParser.return_value
            mock_parser_instance.parse_html_prices.return_value = random_bytes

            with patch('io.BytesIO', return_value=io.BytesIO(random_bytes)) as mock_io:
                result = self.analyzer.parse_raw_data(self.url)

                self.assertEqual(result, random_bytes)
                mock_parser_instance.parse_html_prices.assert_called_once_with(self.url)

    def test_analyzer_initialization(self):
        self.assertEqual(self.analyzer.storage_file, self.storage_file)
        self.assertIsInstance(self.analyzer.storage_file, str)

if __name__ == '__main__':
    unittest.main()