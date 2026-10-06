import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import os
import random
import uuid
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
        random_url = f"https://{uuid.uuid4().hex}.com/api/v1/price"
        expected_price = round(random.uniform(1.0, 1000.0), 4)

        mock_response = MagicMock()
        mock_response.json.return_value = {"price": expected_price}

        with patch("requests.get", return_value=mock_response) as mock_get:
            price = self.parser.fetch_price(random_url)
            mock_get.assert_called_once_with(random_url, timeout=10)
            self.assertEqual(price, expected_price)

    def test_fetch_price_missing_key(self):
        random_url = f"https://{uuid.uuid4().hex}.net/price"

        mock_response = MagicMock()
        mock_response.json.return_value = {}

        with patch("requests.get", return_value=mock_response):
            price = self.parser.fetch_price(random_url)
            self.assertIsNone(price)

    def test_parse_html_prices_success(self):
        random_url = f"https://{uuid.uuid4().hex}.org/market"
        expected_val = round(random.uniform(10.0, 500.0), 2)
        html_content = f"<html><body><span>{expected_val}</span></body></html>"

        mock_response = MagicMock()
        mock_response.text = html_content

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = self.parser.parse_html_prices(random_url)
            mock_get.assert_called_once_with(random_url, timeout=10)
            self.assertEqual(result, float(expected_val))

    def test_parse_html_prices_empty(self):
        random_url = f"https://{uuid.uuid4().hex}.io/empty"

        mock_response = MagicMock()
        mock_response.text = "<html><body></body></html>"

        with patch("requests.get", return_value=mock_response):
            result = self.parser.parse_html_prices(random_url)
            self.assertIsNone(result)

    def test_fetch_and_store(self):
        symbol = uuid.uuid4().hex[:6].upper()
        price = round(random.uniform(50.0, 2500.0), 2)

        self.parser.fetch_and_store(symbol, price)

        conn = sqlite3.connect(self.random_db)
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, price FROM market_data")
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], symbol)
        self.assertEqual(row[1], price)

    def test_load_data_from_db(self):
        symbol1 = uuid.uuid4().hex[:5].upper()
        price1 = round(random.uniform(1.0, 100.0), 2)
        symbol2 = uuid.uuid4().hex[:5].upper()
        price2 = round(random.uniform(101.0, 200.0), 2)

        self.parser.fetch_and_store(symbol1, price1)
        self.parser.fetch_and_store(symbol2, price2)

        data = self.parser.load_data(self.random_db)

        self.assertIn(f"{symbol1},{price1}\n", data)
        self.assertIn(f"{symbol2},{price2}\n", data)

    def test_load_data_from_file(self):
        random_filename = f"{uuid.uuid4().hex}.txt"
        line1 = f"{uuid.uuid4().hex}\n"
        line2 = f"{uuid.uuid4().hex}\n"
        file_bytes = f"{line1}{line2}".encode("utf-8")

        mock_file = io.BytesIO(file_bytes)

        with patch("builtins.open", return_value=mock_file):
            data = self.parser.load_data(random_filename)
            self.assertEqual(data, [line1, line2])


if __name__ == "__main__":
    unittest.main()