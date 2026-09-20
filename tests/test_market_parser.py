import unittest
from unittest.mock import patch, mock_open
import json
import os
import uuid
import random
import string
import requests
import io
from bs4 import BeautifulSoup
from skills.market_parser import MarketParser


class TestMarketParser(unittest.TestCase):

    def setUp(self):
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.parser = MarketParser(storage_file=self.random_storage)

    def tearDown(self):
        if os.path.exists(self.random_storage):
            os.remove(self.random_storage)

    def test_fetch_price_success(self):
        random_url = f"https://{uuid.uuid4().hex}.com/api"
        random_key = uuid.uuid4().hex
        random_val = random.randint(100, 99999)
        expected_response = {random_key: random_val}

        with patch('requests.get') as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = expected_response
            mock_response.raise_for_status.return_value = None

            result = self.parser.fetch_price(random_url)
            self.assertEqual(result, expected_response)
            mock_get.assert_called_once_with(random_url, timeout=10)

    def test_fetch_price_value_error(self):
        random_url = f"https://{uuid.uuid4().hex}.net/data"
        random_error_msg = uuid.uuid4().hex

        with patch('requests.get') as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.side_effect = ValueError(random_error_msg)

            result = self.parser.fetch_price(random_url)
            self.assertIn("error", result)
            self.assertIn(random_error_msg, result["error"])

    def test_fetch_price_request_exception(self):
        random_url = f"https://{uuid.uuid4().hex}.org/fail"

        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException

            result = self.parser.fetch_price(random_url)
            self.assertIsNone(result)

    def test_parse_html_prices_success(self):
        random_url = f"https://{uuid.uuid4().hex}.io/market"
        symbol_name = ''.join(random.choices(string.ascii_uppercase, k=4))
        price_value = f"${random.uniform(10.0, 1000.0):.2f}"

        html_content = f'''
        <html>
            <body>
                <div class="crypto-card">
                    <div class="name">{symbol_name}</div>
                    <div class="price">{price_value}</div>
                </div>
            </body>
        </html>
        '''

        with patch('requests.get') as mock_get:
            mock_response = mock_get.return_value
            mock_response.text = html_content
            mock_response.raise_for_status.return_value = None

            result = self.parser.parse_html_prices(random_url)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["symbol"], symbol_name)
            self.assertEqual(result[0]["price"], price_value)

    def test_parse_html_prices_request_exception(self):
        random_url = f"https://{uuid.uuid4().hex}.io/broken"

        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException

            result = self.parser.parse_html_prices(random_url)
            self.assertEqual(result, [])

    def test_fetch_and_store_new_file(self):
        random_symbol = ''.join(random.choices(string.ascii_uppercase, k=3))
        random_price = str(random.randint(100, 5000))

        record_id = self.parser.fetch_and_store(random_symbol, random_price)
        self.assertTrue(uuid.UUID(record_id))

        self.assertTrue(os.path.exists(self.random_storage))
        with open(self.random_storage, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn(random_symbol, data)
        self.assertEqual(data[random_symbol]["price"], random_price)
        self.assertEqual(data[random_symbol]["record_id"], record_id)

    def test_fetch_and_store_existing_file(self):
        existing_symbol = ''.join(random.choices(string.ascii_uppercase, k=3))
        existing_price = str(random.randint(1, 99))
        existing_id = str(uuid.uuid4())

        initial_data = {
            existing_symbol: {
                "price": existing_price,
                "record_id": existing_id
            }
        }
        with open(self.random_storage, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)

        new_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        new_price = str(random.randint(1000, 9999))

        new_record_id = self.parser.fetch_and_store(new_symbol, new_price)

        with open(self.random_storage, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn(existing_symbol, data)
        self.assertEqual(data[existing_symbol]["record_id"], existing_id)
        self.assertIn(new_symbol, data)
        self.assertEqual(data[new_symbol]["price"], new_price)
        self.assertEqual(data[new_symbol]["record_id"], new_record_id)

    def test_load_data_existing(self):
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        test_data = {random_key: random_val}

        with open(self.random_storage, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        loaded = self.parser.load_data(self.random_storage)
        self.assertEqual(loaded, test_data)

    def test_load_data_nonexistent(self):
        nonexistent_file = f"{uuid.uuid4().hex}.json"
        loaded = self.parser.load_data(nonexistent_file)
        self.assertEqual(loaded, {})


if __name__ == '__main__':
    unittest.main()