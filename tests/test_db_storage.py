import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import tempfile
import os
import uuid
import random
import io
from skills.db_storage import MarketParser

class TestMarketParser(unittest.TestCase):
    def setUp(self):
        self.random_db = f"{uuid.uuid4().hex}.db"
        self.parser = MarketParser(storage_file=self.random_db)

    def tearDown(self):
        if os.path.exists(self.random_db):
            os.remove(self.random_db)

    def test_fetch_price_success(self):
        random_url = f"https://{uuid.uuid4().hex}.com/api"
        expected_price = round(random.uniform(10.0, 1000.0), 2)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"price": expected_price}

        with patch("requests.get", return_value=mock_response) as mock_get:
            price = self.parser.fetch_price(random_url)
            mock_get.assert_called_once_with(random_url, timeout=10)
            self.assertEqual(price, expected_price)

    def test_fetch_price_failure_raises(self):
        random_url = f"https://{uuid.uuid4().hex}.com/api"
        
        with patch("requests.get", side_effect=Exception(uuid.uuid4().hex)):
            with self.assertRaises(Exception):
                self.parser.fetch_price(random_url)

    def test_parse_html_prices_success(self):
        random_url = f"https://{uuid.uuid4().hex}.com/market"
        expected_price = round(random.uniform(1.0, 500.0), 4)
        html_content = f"<html><body><span>{expected_price}</span></body></html>"
        
        mock_response = MagicMock()
        mock_response.text = html_content

        with patch("requests.get", return_value=mock_response) as mock_get:
            price = self.parser.parse_html_prices(random_url)
            mock_get.assert_called_once_with(random_url, timeout=10)
            self.assertEqual(price, expected_price)

    def test_parse_html_prices_empty_element(self):
        random_url = f"https://{uuid.uuid4().hex}.com/market"
        mock_response = MagicMock()
        mock_response.text = "<html><body></body></html>"

        with patch("requests.get", return_value=mock_response):
            price = self.parser.parse_html_prices(random_url)
            self.assertIsNone(price)

    def test_fetch_and_store(self):
        random_symbol = uuid.uuid4().hex[:5].upper()
        random_price = round(random.uniform(100.0, 5000.0), 2)

        self.parser.fetch_and_store(random_symbol, random_price)

        conn = sqlite3.connect(self.random_db)
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, price FROM market_data")
        rows = cursor.fetchall()
        conn.close()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], random_symbol)
        self.assertEqual(rows[0][1], random_price)

    def test_load_data_db(self):
        random_symbol = uuid.uuid4().hex[:4].upper()
        random_price = round(random.uniform(10.0, 100.0), 2)

        self.parser.fetch_and_store(random_symbol, random_price)

        data = self.parser.load_data(self.random_db)
        self.assertIn(f"{random_symbol},{random_price}\n", data)

    def test_load_data_file(self):
        random_filename = f"{uuid.uuid4().hex}.txt"
        random_text = f"{uuid.uuid4().hex}:{random.uniform(1, 100)}"
        
        mock_file_data = io.BytesIO(random_text.encode('utf-8'))

        with patch("builtins.open", return_value=mock_file_data):
            lines = self.parser.load_data(random_filename)
            self.assertEqual(lines, [random_text])

    def test_load_data_db_error_raises(self):
        invalid_db_name = f"{uuid.uuid4().hex}.db"
        
        with self.assertRaises(Exception):
            self.parser.load_data(invalid_db_name)

if __name__ == "__main__":
    unittest.main()