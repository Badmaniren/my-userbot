import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
from skills.price_alerter import MarketParser

class TestMarketParser(unittest.TestCase):
    def setUp(self):
        self.random_storage_file = f"{uuid.uuid4().hex}.json"
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_price = round(random.uniform(10.0, 50000.0), 2)
        self.random_url = f"https://{uuid.uuid4().hex}.com/market/{self.random_symbol.lower()}"

    def test_init_sets_storage_file(self):
        parser = MarketParser(self.random_storage_file)
        self.assertEqual(parser.storage_file, self.random_storage_file)

    def test_fetch_price_success(self):
        parser = MarketParser(self.random_storage_file)
        random_content = f"<html><body><span class='price'>{self.random_price}</span></body></html>"

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = random_content
            mock_get.return_value = mock_response

            price = parser.fetch_price(self.random_url)
            self.assertEqual(price, self.random_price)
            mock_get.assert_called_once_with(self.random_url, timeout=10)

    def test_fetch_price_request_exception(self):
        parser = MarketParser(self.random_storage_file)

        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception(uuid.uuid4().hex)
            price = parser.fetch_price(self.random_url)
            self.assertIsNone(price)

    def test_parse_html_prices_valid_data(self):
        parser = MarketParser(self.random_storage_file)
        random_html = f"<div>ID: {self.random_symbol} Price: {self.random_price}</div>"

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = random_html
            mock_get.return_value = mock_response

            parsed_data = parser.parse_html_prices(self.random_url)
            self.assertIn(self.random_symbol, str(parsed_data))

    def test_fetch_and_store_saves_data(self):
        parser = MarketParser(self.random_storage_file)

        with patch.object(parser, 'load_data', return_value={}) as mock_load, \
             patch('builtins.open', create=True) as mock_open:

            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            parser.fetch_and_store(self.random_symbol, self.random_price)
            mock_load.assert_called_once_with(self.random_storage_file)
            mock_open.assert_called_once()
            mock_file.write.assert_called()

    def test_load_data_reads_file_correctly(self):
        parser = MarketParser(self.random_storage_file)
        random_json_content = f'{{"{self.random_symbol}": {self.random_price}}}'

        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', create=True) as mock_open:

            mock_open.return_value.__enter__.return_value = io.BytesIO(random_json_content.encode('utf-8'))

            data = parser.load_data(self.random_storage_file)
            self.assertIsInstance(data, dict)

    def test_load_data_file_not_exists(self):
        parser = MarketParser(self.random_storage_file)

        with patch('os.path.exists', return_value=False):
            data = parser.load_data(self.random_storage_file)
            self.assertEqual(data, {})

if __name__ == '__main__':
    unittest.main()