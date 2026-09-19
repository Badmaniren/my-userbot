import unittest
import uuid
import random
import os
from skills.market_parser import MarketParser

class TestMarketParserIntegration(unittest.TestCase):
    def setUp(self):
        self.parser = MarketParser()
        self.test_symbol = f"COIN_{uuid.uuid4().hex[:6].upper()}"
        self.test_price = round(random.uniform(10.0, 50000.0), 2)
        self.output_filename = f"market_data_{uuid.uuid4().hex}.json"
        self.parser.storage_file = self.output_filename

    def tearDown(self):
        if os.path.exists(self.output_filename):
            os.remove(self.output_filename)

    def test_market_parser_real_execution(self):
        result_id = self.parser.fetch_and_store(self.test_symbol, self.test_price)
        
        self.assertIsNotNone(result_id)
        self.assertIsInstance(result_id, str)
        
        self.assertTrue(os.path.exists(self.output_filename), "Файл с данными рынка не был создан")
        
        loaded_data = self.parser.load_data(self.output_filename)
        self.assertIn(self.test_symbol, loaded_data)
        self.assertEqual(loaded_data[self.test_symbol]["price"], self.test_price)
        self.assertEqual(loaded_data[self.test_symbol]["record_id"], result_id)

if __name__ == "__main__":
    unittest.main()