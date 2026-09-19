import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
from skills.db_storage import MarketParser

class TestMarketParser(unittest.TestCase):
    def setUp(self):
        self.random_storage = f"{uuid.uuid4().hex}.db"
        self.parser = MarketParser(storage_file=self.random_storage)

    def test_init_sets_storage(self):
        self.assertEqual(self.parser.storage_file, self.random_storage)

    def test_fetch_price_success(self):
        random_url = f"https://{uuid.uuid4().hex}.com/api"
        expected_price = round(random.uniform(10.0, 10000.0), 2)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"price": expected_price}

        with patch('requests.get', return_value=mock_response) as mock_get:
            price = self.parser.fetch_price(random_url)
            mock_get.assert_called_once_with(random_url, timeout=10)
            self.assertEqual(price, expected_price)

    def test_fetch_price_network_error(self):
        random_url = f"https://{uuid.uuid4().hex}.net/fail"
        with patch('requests.get', side_effect=Exception(uuid.uuid4().hex)) as mock_get:
            price = self.parser.fetch_price(random_url)
            mock_get.assert_called_once_with(random_url, timeout=10)
            self.assertIsNone(price)

    def test_parse_html_prices(self):
        random_url = f"https://{uuid.uuid4().hex}.org/market"
        random_price_str = f"{random.randint(100, 999)}.{random.randint(10, 99)}"
        random_tag_id = uuid.uuid4().hex
        html_content = f'<html><body><div id="{random_tag_id}">{random_price_str}</div></body></html>'
        
        mock_response = MagicMock()
        mock_response.text = html_content

        with patch('requests.get', return_value=mock_response) as mock_get:
            with patch('bs4.BeautifulSoup') as mock_bs:
                mock_soup = MagicMock()
                mock_element = MagicMock()
                mock_element.text = random_price_str
                mock_soup.find.return_value = mock_element
                mock_bs.return_value = mock_soup

                price = self.parser.parse_html_prices(random_url)
                mock_get.assert_called_once_with(random_url, timeout=10)
                self.assertEqual(price, float(random_price_str))

    def test_fetch_and_store(self):
        random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        random_price = round(random.uniform(1.0, 500.0), 4)

        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            self.parser.fetch_and_store(symbol=random_symbol, price=random_price)

            mock_connect.assert_called_once_with(self.random_storage)
            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called_once()
            mock_conn.close.assert_called_once()

    def test_load_data(self):
        random_filename = f"{uuid.uuid4().hex}.csv"
        random_row_data = f"{uuid.uuid4().hex},{random.uniform(1, 100)}\n"
        mock_bytes = io.BytesIO(random_row_data.encode('utf-8'))

        with patch('builtins.open', return_value=mock_bytes) as mock_file:
            data = self.parser.load_data(random_filename)
            mock_file.assert_called_once_with(random_filename, 'rb')
            self.assertIn(random_row_data.strip(), ''.join(data))

if __name__ == '__main__':
    unittest.main()