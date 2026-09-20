import unittest
import os
import uuid
import random
from skills.market_report_generator import generate_market_report
from skills.market_parser import MarketParser
from skills.db_storage import load_data, fetch_and_store

class TestMarketReportGeneratorIntegration(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_db_{self.random_suffix}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.test_price = round(random.uniform(10.0, 1000.0), 2)
        self.parser = MarketParser(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_report_generator_integration(self):
        fetch_and_store(self.symbol, self.test_price)
        
        report = generate_market_report(self.storage_file, self.symbol)
        
        self.assertIsNotNone(report)
        self.assertIn(str(self.symbol), str(report))
        self.assertIn(str(self.test_price), str(report))
        
        loaded_data = load_data(self.storage_file)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.test_price)

if __name__ == '__main__':
    unittest.main()