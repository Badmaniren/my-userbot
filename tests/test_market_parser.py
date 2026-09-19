import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import requests
from skills.market_parser import MarketParser

class TestMarketParser(unittest.TestCase):

    def setUp(self):
        self.parser = MarketParser()

    def test_fetch_market_data_success(self):
        random_crypto = ''.join(random.choices(string.ascii_uppercase, k=random.randint(3, 6)))
        random_price = round(random.uniform(10.0, 99999.99), 2)
        random_url = f"https://{uuid.uuid4().hex}.com/api/{random_crypto.lower()}"

        mock_response_data = {
            "symbol": random_crypto,
            "price": str(random_price)
        }

        with patch('skills.market_parser.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_get.return_value = mock_resp

            result = self.parser.fetch_price(random_url)

            mock_get.assert_called_once_with(random_url, timeout=unittest.mock.ANY)
            self.assertEqual(result.get("symbol"), random_crypto)
            self.assertEqual(float(result.get("price")), random_price)

    def test_parse_html_page_content(self):
        random_token = uuid.uuid4().hex[:8].upper()
        random_val = round(random.uniform(1.0, 500.0), 4)
        
        html_payload = f"<html><body><div class='crypto-card'><span class='name'>{random_token}</span><span class='price'>{random_val}</span></div></body></html>"
        
        random_stream = io.BytesIO(html_payload.encode('utf-8'))

        with patch('skills.market_parser.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = random_stream.read()
            mock_resp.text = html_payload
            mock_get.return_value = mock_resp

            parsed_items = self.parser.parse_html_prices(f"https://{uuid.uuid4().hex}.net")

            self.assertTrue(isinstance(parsed_items, list))
            matched_item = next((item for item in parsed_items if item.get("symbol") == random_token), None)
            self.assertIsNotNone(matched_item)
            self.assertEqual(float(matched_item.get("price")), random_val)

    def test_fetch_price_network_failure(self):
        random_url = f"https://{uuid.uuid4().hex}.org/failure"

        with patch('skills.market_parser.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException(uuid.uuid4().hex)

            result = self.parser.fetch_price(random_url)

            self.assertIsNone(result)

    def test_parse_invalid_response_structure(self):
        random_url = f"https://{uuid.uuid4().hex}.io/bad"
        random_garbage = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))

        with patch('skills.market_parser.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = random_garbage.read().decode('utf-8')
            mock_resp.json.side_effect = ValueError(uuid.uuid4().hex)
            mock_get.return_value = mock_resp

            result = self.parser.fetch_price(random_url)

            self.assertIn("error", result)

if __name__ == '__main__':
    unittest.main()