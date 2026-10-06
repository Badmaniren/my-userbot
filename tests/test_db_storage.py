import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import os
import io
import random
import uuid
from skills.db_storage import MarketParser


class TestMarketParserInquisitor(unittest.TestCase):

    def setUp(self):
        self.random_db = f"{uuid.uuid4().hex}.db"
        self.parser = MarketParser(storage_file=self.random_db)

    def tearDown(self):
        if os.path.exists(self.random_db):
            os.remove(self.random_db)

    def test_fetch_price_valid_json(self):
        random_url = f"https://{uuid.uuid4().hex}.com/api"
        expected_price = round(random.uniform(1.0, 1000.0), 2)

        mock_response = MagicMock()
        mock_response.json.return_value = {"price": expected_price}

        with patch('requests.get', return_value=mock_response) as mock_get:
            price = self.parser.fetch_price(random_url)
            mock_get.assert_called_once_with(random_url, timeout=10)
            self.assertEqual(price, expected_price)

    def test_fetch_price_invalid_structure(self):
        random_url = f"https://{uuid.uuid4().hex}.net/feed"

        mock_response = MagicMock()
        mock_response.json.return_value = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch('requests.get', return_value=mock_response):
            price = self.parser.fetch_price(random_url)
            self.assertIsNone(price)

    def test_parse_html_prices_valid_element(self):
        random_url = f"https://{uuid.uuid4().hex}.org/market"
        raw_price = round(random.uniform(10.0, 5000.0), 4)

        mock_response = MagicMock()
        mock_response.text = f"<html><body><span>{raw_price}</span></body></html>"

        with patch('requests.get', return_value=mock_response) as mock_get:
            result = self.parser.parse_html_prices(random_url)
            mock_get.assert_called_once_with(random_url, timeout=10)
            self.assertEqual(result, float(raw_price))

    def test_parse_html_prices_empty_element(self):
        random_url = f"https://{uuid.uuid4().hex}.io/empty"

        mock_response = MagicMock()
        mock_response.text = "<html><body></body></html>"

        with patch('requests.get', return_value=mock_response):
            result = self.parser.parse_html_prices(random_url)
            self.assertIsNone(result)

    def test_fetch_and_store_success_and_integrity(self):
        symbol = uuid.uuid4().hex[:8].upper()
        price = round(random.uniform(50.0, 500.0), 2)

        self.parser.fetch_and_store(symbol, price)

        self.assertTrue(os.path.exists(self.random_db))

        conn = sqlite3.connect(self.random_db)
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, price FROM market_data")
        rows = cursor.fetchall()
        conn.close()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], symbol)
        self.assertEqual(rows[0][1], price)

    def test_fetch_and_store_strict_typing_violation(self):
        symbol = random.randint(1000, 9999)
        price = f"invalid_price_{uuid.uuid4().hex[:4]}"

        with self.assertRaises((sqlite3.IntegrityError, TypeError, ValueError)):
            self.parser.fetch_and_store(symbol, price)

    def test_load_data_from_database(self):
        symbol = uuid.uuid4().hex[:6].upper()
        price = round(random.uniform(1.0, 100.0), 2)

        self.parser.fetch_and_store(symbol, price)

        loaded = self.parser.load_data(self.random_db)
        self.assertIsInstance(loaded, list)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0], f"{symbol},{price}\n")

    def test_load_data_from_file_stream(self):
        random_filename = f"{uuid.uuid4().hex}.txt"
        expected_line = f"{uuid.uuid4().hex}:{random.uniform(1, 100)}\n"
        stream_data = io.BytesIO(expected_line.encode('utf-8'))

        with patch('builtins.open', return_value=stream_data):
            loaded = self.parser.load_data(random_filename)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0], expected_line)


if __name__ == '__main__':
    unittest.main()