import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import string
import io
import requests
from skills.market_parser import MarketParser


class TestMarketParser(unittest.TestCase):

    def setUp(self):
        self.random_filename = f"{uuid.uuid4().hex}.json"
        self.parser = MarketParser(storage_file=self.random_filename)

    def tearDown(self):
        if os.path.exists(self.random_filename):
            os.remove(self.random_filename)

    def test_fetch_price_success_json(self):
        random_url = f"https://{''.join(random.choices(string.ascii_lowercase, k=10))}.com/{uuid.uuid4().hex}"
        random_key = uuid.uuid4().hex
        random_val = random.randint(100, 100000)
        mock_response_data = {random_key: random_val}

        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response_data
            mock_get.return_value = mock_resp

            result = self.parser.fetch_price(random_url)
            self.assertEqual(result, mock_response_data)
            mock_get.assert_called_once_with(random_url, timeout=10)

    def test_fetch_price_value_error_json(self):
        random_url = f"https://{''.join(random.choices(string.ascii_lowercase, k=10))}.com/{uuid.uuid4().hex}"
        random_error_text = uuid.uuid4().hex

        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.side_effect = ValueError(random_error_text)
            mock_get.return_value = mock_resp

            result = self.parser.fetch_price(random_url)
            self.assertIn("error", result)
            self.assertIn(random_error_text, result["error"])

    def test_fetch_price_request_exception(self):
        random_url = f"https://{''.join(random.choices(string.ascii_lowercase, k=10))}.com/{uuid.uuid4().hex}"

        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException

            result = self.parser.fetch_price(random_url)
            self.assertIsNone(result)

    def test_parse_html_prices_success(self):
        random_url = f"https://{''.join(random.choices(string.ascii_lowercase, k=10))}.com/{uuid.uuid4().hex}"
        sym1 = uuid.uuid4().hex[:5].upper()
        pr1 = str(random.randint(1, 10000))
        sym2 = uuid.uuid4().hex[:5].upper()
        pr2 = str(random.randint(1, 10000))

        html_content = f"""
        <html>
            <body>
                <div class="crypto-card">
                    <div class="name">{sym1}</div>
                    <div class="price">{pr1}</div>
                </div>
                <div class="crypto-card">
                    <div class="name">{sym2}</div>
                    <div class="price">{pr2}</div>
                </div>
            </body>
        </html>
        """

        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.text = html_content
            mock_get.return_value = mock_resp

            items = self.parser.parse_html_prices(random_url)
            self.assertEqual(len(items), 2)
            self.assertEqual(items[0]["symbol"], sym1)
            self.assertEqual(items[0]["price"], pr1)
            self.assertEqual(items[1]["symbol"], sym2)
            self.assertEqual(items[1]["price"], pr2)

    def test_parse_html_prices_exception(self):
        random_url = f"https://{''.join(random.choices(string.ascii_lowercase, k=10))}.com/{uuid.uuid4().hex}"

        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException
            items = self.parser.parse_html_prices(random_url)
            self.assertEqual(items, [])

    def test_fetch_and_store_new_file(self):
        sym = uuid.uuid4().hex[:6]
        price = random.uniform(10.0, 500.0)

        record_id = self.parser.fetch_and_store(sym, price)
        self.assertTrue(os.path.exists(self.random_filename))

        with open(self.random_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn(sym, data)
        self.assertEqual(data[sym]["price"], price)
        self.assertEqual(data[sym]["record_id"], record_id)

    def test_fetch_and_store_corrupted_file(self):
        random_garbage = uuid.uuid4().hex.encode('utf-8')
        with open(self.random_filename, 'wb') as f:
            f.write(random_garbage)

        sym = uuid.uuid4().hex[:6]
        price = random.randint(1, 9999)

        record_id = self.parser.fetch_and_store(sym, price)

        with open(self.random_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn(sym, data)
        self.assertEqual(data[sym]["record_id"], record_id)

    def test_load_data_exists(self):
        sym = uuid.uuid4().hex[:6]
        val = uuid.uuid4().hex
        initial_data = {sym: {"value": val}}

        with open(self.random_filename, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)

        loaded = self.parser.load_data(self.random_filename)
        self.assertEqual(loaded, initial_data)

    def test_load_data_not_exists(self):
        non_existent = f"{uuid.uuid4().hex}.json"
        loaded = self.parser.load_data(non_existent)
        self.assertEqual(loaded, {})


if __name__ == '__main__':
    unittest.main()