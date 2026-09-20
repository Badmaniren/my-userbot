import unittest
import os
import json
import uuid
import random
from skills.market_parser import MarketParser

class TestMarketParserIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_filename = f"test_market_storage_{self.random_suffix}.json"
        self.parser = MarketParser(storage_file=self.storage_filename)

    def tearDown(self):
        if os.path.exists(self.storage_filename):
            try:
                os.remove(self.storage_filename)
            except OSError:
                pass

    def test_fetch_and_store_integration(self):
        random_symbol = f"COIN_{uuid.uuid4().hex[:6].upper()}"
        random_price = round(random.uniform(10.0, 50000.0), 2)

        record_id = self.parser.fetch_and_store(random_symbol, random_price)
        
        self.assertIsInstance(record_id, str)
        self.assertTrue(len(record_id) > 0)
        self.assertTrue(os.path.exists(self.storage_filename))

        loaded_data = self.parser.load_data(self.storage_filename)
        self.assertIn(random_symbol, loaded_data)
        self.assertEqual(loaded_data[random_symbol]["price"], random_price)
        self.assertEqual(loaded_data[random_symbol]["record_id"], record_id)

    def test_parse_html_prices_invalid_url(self):
        random_invalid_url = f"http://nonexistent-domain-{uuid.uuid4().hex}.local/api"
        result = self.parser.parse_html_prices(random_invalid_url)
        self.assertEqual(result, [])

    def test_fetch_price_invalid_url(self):
        random_invalid_url = f"http://nonexistent-domain-{uuid.uuid4().hex}.local/api"
        result = self.parser.fetch_price(random_invalid_url)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()