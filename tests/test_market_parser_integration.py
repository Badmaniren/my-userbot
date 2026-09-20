import unittest
import os
import json
import uuid
import random
from skills.market_parser import MarketParser

class TestMarketParserIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_storage_{self.random_suffix}.json"
        self.parser = MarketParser(storage_file=self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_fetch_and_store_integration(self):
        random_symbol = f"SYM_{random.randint(1000, 9999)}"
        random_price = round(random.uniform(10.0, 1500.0), 2)

        record_id = self.parser.fetch_and_store(symbol=random_symbol, price=random_price)

        self.assertIsInstance(record_id, str)
        self.assertTrue(len(record_id) > 0)
        self.assertTrue(os.path.exists(self.storage_file))

        loaded_data = self.parser.load_data(self.storage_file)

        self.assertIn(random_symbol, loaded_data)
        self.assertEqual(loaded_data[random_symbol]["price"], random_price)
        self.assertEqual(loaded_data[random_symbol]["record_id"], record_id)

    def test_load_nonexistent_data(self):
        non_existent_file = f"non_existent_{uuid.uuid4().hex}.json"
        data = self.parser.load_data(non_existent_file)
        self.assertEqual(data, {})

if __name__ == "__main__":
    unittest.main()