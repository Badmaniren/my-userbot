import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import string
import json
import os
import requests
from skills.market_parser import MarketParser


class TestMarketParser(unittest.TestCase):

    def setUp(self):
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.parser = MarketParser(storage_file=self.random_storage)

    def tearDown(self):
        if os.path.exists(self.random_storage):
            try:
                os.remove(self.random_storage)
            except OSError:
                pass

    def test_fetch_price_json_success(self):
        random_url = f"https://{uuid.uuid4().hex}.com/api"
        random_key = uuid.uuid4().hex
        random_val = random.randint(1000, 99999)
        mock_response_data = {random_key: random_val}

        with patch('requests.get') as mock_get:
            mock_resp = mock_get.return_value
            mock_resp.json.return_value = mock_response_data

            result = self.parser.fetch_price(random_url)
            self.assertEqual(result, mock_response_data)
            mock_get.assert_called_once_with(random_url, timeout=10)

    def test_fetch_price_value_error_json(self):
        random_url = f"https://{uuid.uuid4().hex}.net/data"

        with patch('requests.get') as mock_get:
            mock_resp = mock_get.return_value
            mock_resp.json.side_effect = ValueError(uuid.uuid4().hex)

            result = self.parser.fetch_price(random_url)
            self.assertIn("error", result)

    def test_fetch_price_request_exception(self):
        random_url = f"https://{uuid.uuid4().hex}.org/fail"

        with patch('requests.get', side_effect=requests.exceptions.RequestException):
            result = self.parser.fetch_price(random_url)
            self.assertIsNone(result)

    def test_parse_html_prices_success(self):
        random_url = f"https://{uuid.uuid4().hex}.io/market"
        crypto_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        crypto_price = str(random.randint(10, 10000))

        html_content = f"""
        <html>
            <body>
                <div class="crypto-card">
                    <div class="name">{crypto_symbol}</div>
                    <div class="price">{crypto_price}</div>
                </div>
            </body>
        </html>
        """

        with patch('requests.get') as mock_get:
            mock_resp = mock_get.return_value
            mock_resp.text = html_content

            parsed = self.parser.parse_html_prices(random_url)
            self.assertEqual(len(parsed), 1)
            self.assertEqual(parsed[0]["symbol"], crypto_symbol)
            self.assertEqual(parsed[0]["price"], crypto_price)

    def test_parse_html_prices_request_exception(self):
        random_url = f"https://{uuid.uuid4().hex}.io/error"

        with patch('requests.get', side_effect=requests.exceptions.RequestException):
            parsed = self.parser.parse_html_prices(random_url)
            self.assertEqual(parsed, [])

    def test_fetch_and_store_without_existing_file(self):
        symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        price = str(random.uniform(0.1, 999.9))

        with patch('os.path.exists', return_value=False), \
             patch('builtins.open', mock_open()) as mock_file:
            
            record_id = self.parser.fetch_and_store(symbol, price)
            self.assertIsInstance(record_id, str)
            self.assertTrue(len(record_id) > 0)
            mock_file.assert_called()

    def test_fetch_and_store_with_existing_file(self):
        symbol = ''.join(random.choices(string.ascii_uppercase, k=3))
        price = str(random.randint(1, 500))
        existing_symbol = ''.join(random.choices(string.ascii_uppercase, k=3))
        existing_data = {existing_symbol: {"price": "123", "record_id": uuid.uuid4().hex}}

        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(existing_data))) as mock_file:

            record_id = self.parser.fetch_and_store(symbol, price)
            self.assertIsInstance(record_id, str)
            mock_file.assert_called()

    def test_load_data_exists(self):
        random_filename = f"{uuid.uuid4().hex}.json"
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        file_content = json.dumps({random_key: random_val})

        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=file_content)):
            
            data = self.parser.load_data(random_filename)
            self.assertEqual(data.get(random_key), random_val)

    def test_load_data_not_exists(self):
        random_filename = f"{uuid.uuid4().hex}.json"

        with patch('os.path.exists', return_value=False):
            data = self.parser.load_data(random_filename)
            self.assertEqual(data, {})


if __name__ == '__main__':
    unittest.main()