import unittest
import os
import tempfile
import uuid
import random
from skills.market_parser import MarketParser

class TestMarketParserIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_path = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4()}.json")
        self.parser = MarketParser(storage_file=self.storage_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_fetch_and_store_integration(self):
        random_symbol = f"COIN_{uuid.uuid4().hex[:6].upper()}"
        random_price = round(random.uniform(1.0, 100000.0), 2)

        record_id = self.parser.fetch_and_store(random_symbol, random_price)
        
        self.assertIsInstance(record_id, str)
        self.assertTrue(len(record_id) > 0)

        self.assertTrue(os.path.exists(self.storage_path))

        loaded_data = self.parser.load_data(self.storage_path)
        self.assertIn(random_symbol, loaded_data)
        self.assertEqual(loaded_data[random_symbol]["price"], random_price)
        self.assertEqual(loaded_data[random_symbol]["record_id"], record_id)

    def test_invalid_url_handling(self):
        random_url = f"http://nonexistent-domain-{uuid.uuid4()}.local/api"
        
        json_result = self.parser.fetch_price(random_url)
        self.assertIsNone(json_result)

        html_result = self.parser.parse_html_prices(random_url)
        self.assertEqual(html_result, [])

if __name__ == '__main__':
    unittest.main()