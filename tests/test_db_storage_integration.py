import unittest
import os
import uuid
import random
from skills.db_storage import MarketParser

class TestDbStorageIntegration(unittest.TestCase):
    def setUp(self):
        self.db_filename = f"test_market_{uuid.uuid4()}.db"
        self.parser = MarketParser(storage_file=self.db_filename)

    def tearDown(self):
        if os.path.exists(self.db_filename):
            os.remove(self.db_filename)

    def test_market_parser_storage_integration(self):
        test_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        test_price = round(random.uniform(10.0, 1000.0), 2)

        self.parser.fetch_and_store(symbol=test_symbol, price=test_price)

        loaded_data = self.parser.load_data(self.db_filename)

        self.assertIsInstance(loaded_data, list)
        self.assertGreater(len(loaded_data), 0)

        found = False
        expected_row = f"{test_symbol},{test_price}\n"
        for row in loaded_data:
            if row.strip() == expected_row.strip():
                found = True
                break

        self.assertTrue(found, f"Expected data '{expected_row.strip()}' not found in loaded storage data: {loaded_data}")

if __name__ == '__main__':
    unittest.main()