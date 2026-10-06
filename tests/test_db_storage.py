import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import os
import uuid
import random
import io
import requests
from bs4 import BeautifulSoup
from skills.db_storage import MarketParser

class TestMarketParserInquisitor(unittest.TestCase):

    def setUp(self):
        self.db_filename = f"{uuid.uuid4().hex}.db"
        self.parser = MarketParser(storage_file=self.db_filename)

    def tearDown(self):
        if os.path.exists(self.db_filename):
            try:
                os.remove(self.db_filename)
            except OSError:
                pass

    def test_fetch_price_success(self):
        target_url = f"https://{uuid.uuid4().hex}.com/api/v1/price"
        expected_price = round(random.uniform(10.0, 5000.0), 4)
        mock_response_data = {"price": expected_price}

        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response_data
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            price = self.parser.fetch_price(target_url)

            mock_get.assert_called_once_with(target_url, timeout=10)
            self.assertEqual(price, expected_price)

    def test_parse_html_prices_valid(self):
        target_url = f"https://{uuid.uuid4().hex}.com/market/asset"
        expected_val = round(random.uniform(1.0, 999.99), 2)
        html_content = f"<html><body><span>{expected_val}</span></body></html>"

        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.text = html_content
            mock_get.return_value = mock_resp

            val = self.parser.parse_html_prices(target_url)

            mock_get.assert_called_once_with(target_url, timeout=10)
            self.assertEqual(val, float(expected_val))

    def test_parse_html_prices_empty(self):
        target_url = f"https://{uuid.uuid4().hex}.com/market/empty"
        html_content = "<html><body></body></html>"

        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.text = html_content
            mock_get.return_value = mock_resp

            val = self.parser.parse_html_prices(target_url)

            self.assertIsNone(val)

    def test_fetch_and_store_and_load_database(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        price = round(random.uniform(100.0, 9999.0), 2)

        self.parser.fetch_and_store(symbol, price)

        loaded_data = self.parser.load_data(self.db_filename)
        
        self.assertIsInstance(loaded_data, list)
        self.assertTrue(len(loaded_data) > 0)
        
        found = False
        expected_row_str = f"{symbol},{price}\n"
        for row_str in loaded_data:
            if symbol in row_str and str(price) in row_str:
                found = True
                self.assertEqual(row_str, expected_row_str)
                break
        
        self.assertTrue(found, f"Stored entry {expected_row_str} not found in loaded data: {loaded_data}")

    def test_load_data_non_db_file(self):
        txt_filename = f"{uuid.uuid4().hex}.txt"
        random_lines = [f"{uuid.uuid4().hex}:{random.random()}\n" for _ in range(3)]
        binary_content = "".join(random_lines).encode('utf-8')

        mock_file_data = io.BytesIO(binary_content)

        with patch('builtins.open', return_value=mock_file_data) as mock_open:
            data = self.parser.load_data(txt_filename)
            
            mock_open.assert_called_once_with(txt_filename, 'rb')
            self.assertEqual(len(data), len(random_lines))
            for idx, decoded_line in enumerate(data):
                self.assertEqual(decoded_line, random_lines[idx])

    def test_fetch_price_request_exception(self):
        target_url = f"https://{uuid.uuid4().hex}.com/fail"
        with patch('requests.get', side_effect=requests.RequestException("Connection error")):
            with self.assertRaises(requests.RequestException):
                self.parser.fetch_price(target_url)

    def test_fetch_and_store_strict_schema_validation(self):
        symbol = f"TICK_{uuid.uuid4().hex[:4]}"
        price = round(random.uniform(0.1, 50.0), 4)

        self.parser.fetch_and_store(symbol, price)

        conn = sqlite3.connect(self.db_filename)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(market_data)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        conn.close()

        self.assertIn("id", columns)
        self.assertIn("symbol", columns)
        self.assertIn("price", columns)
        self.assertEqual(columns["symbol"].upper(), "TEXT")
        self.assertEqual(columns["price"].upper(), "REAL")

if __name__ == '__main__':
    unittest.main()