import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import io
import uuid
import random
import string
from skills.db_storage import MarketParser


class TestMarketParserInquisitor(unittest.TestCase):

    def setUp(self):
        self.random_storage = f"{uuid.uuid4().hex}.db"
        self.parser = MarketParser(storage_file=self.random_storage)

    def tearDown(self):
        with patch('os.remove') as mock_remove:
            pass

    def test_fetch_price_success(self):
        random_url = f"https://{uuid.uuid4().hex}.com/api/price"
        expected_price = round(random.uniform(10.0, 5000.0), 2)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"price": expected_price}
        
        with patch('skills.db_storage.requests.get', return_value=mock_response) as mock_get:
            price = self.parser.fetch_price(random_url)
            mock_get.assert_called_once_with(random_url, timeout=10)
            self.assertEqual(price, expected_price)

    def test_fetch_price_invalid_response_raises(self):
        random_url = f"https://{uuid.uuid4().hex}.com/api/bad"
        
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError(uuid.uuid4().hex)
        
        with patch('skills.db_storage.requests.get', return_value=mock_response):
            with self.assertRaises(Exception):
                self.parser.fetch_price(random_url)

    def test_parse_html_prices_success(self):
        random_url = f"https://{uuid.uuid4().hex}.com/market"
        random_price_val = round(random.uniform(1.0, 999.0), 2)
        html_content = f"<html><body><span>{random_price_val}</span></body></html>"
        
        mock_response = MagicMock()
        mock_response.text = html_content
        
        with patch('skills.db_storage.requests.get', return_value=mock_response) as mock_get:
            price = self.parser.parse_html_prices(random_url)
            mock_get.assert_called_once_with(random_url, timeout=10)
            self.assertEqual(price, float(random_price_val))

    def test_parse_html_prices_empty_element(self):
        random_url = f"https://{uuid.uuid4().hex}.com/empty"
        mock_response = MagicMock()
        mock_response.text = "<html><body></body></html>"
        
        with patch('skills.db_storage.requests.get', return_value=mock_response):
            price = self.parser.parse_html_prices(random_url)
            self.assertIsNone(price)

    def test_fetch_and_store_pipeline(self):
        random_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        random_price = round(random.uniform(50.0, 500.0), 2)
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('skills.db_storage.sqlite3.connect', return_value=mock_conn) as mock_connect:
            self.parser.fetch_and_store(random_symbol, random_price)
            
            mock_connect.assert_called_once_with(self.random_storage)
            self.assertEqual(mock_cursor.execute.call_count, 2)
            mock_conn.commit.assert_called_once()
            mock_conn.close.assert_called_once()

    def test_load_data_db_branch(self):
        db_filename = f"{uuid.uuid4().hex}.db"
        random_symbol = uuid.uuid4().hex[:5]
        random_price = round(random.uniform(1.0, 100.0), 2)
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(random_symbol, random_price)]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('skills.db_storage.sqlite3.connect', return_value=mock_conn) as mock_connect:
            result = self.parser.load_data(db_filename)
            mock_connect.assert_called_once_with(db_filename)
            mock_cursor.execute.assert_called_once_with('SELECT symbol, price FROM market_data')
            mock_conn.close.assert_called_once()
            self.assertIn(f"{random_symbol},{random_price}\n", result)

    def test_load_data_file_branch(self):
        txt_filename = f"{uuid.uuid4().hex}.txt"
        random_line_content = f"{uuid.uuid4().hex},{random.randint(1, 1000)}\n"
        byte_stream = io.BytesIO(random_line_content.encode('utf-8'))
        
        with patch('skills.db_storage.open', return_value=byte_stream) as mock_file:
            result = self.parser.load_data(txt_filename)
            mock_file.assert_called_once_with(txt_filename, 'rb')
            self.assertEqual(result, [random_line_content])


if __name__ == '__main__':
    unittest.main()