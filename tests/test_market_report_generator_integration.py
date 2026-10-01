import unittest
import os
import uuid
import random
from skills.market_report_generator import MarketReportGenerator, generate_market_report
from skills.market_parser import MarketParser
from skills import db_storage

class TestMarketReportGeneratorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_market_storage_{self.test_id}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.price_val = round(random.uniform(10.0, 1000.0), 2)
        
        if hasattr(db_storage, "save_data"):
            db_storage.save_data(self.storage_file, [{
                "symbol": self.symbol,
                "price": self.price_val
            }])
        elif hasattr(db_storage, "save_db"):
            db_storage.save_db(self.storage_file, {
                self.symbol: self.price_val
            })
        else:
            parser = MarketParser(self.storage_file)
            parser.fetch_and_store(self.symbol, self.price_val)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_integration_generate_symbol_report(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        report = generator.generate_symbol_report(self.symbol)
        
        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("count"), 1)
        self.assertEqual(report.get("min_price"), self.price_val)
        self.assertEqual(report.get("max_price"), self.price_val)
        self.assertTrue(report.get(self.symbol))

    def test_integration_global_generate_market_report(self):
        result_str = generate_market_report(self.storage_file, self.symbol)
        
        self.assertIsInstance(result_str, str)
        self.assertIn(self.symbol, result_str)
        self.assertIn(str(self.price_val), result_str)

    def test_integration_update_and_fetch_report(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        new_price = round(random.uniform(1000.0, 5000.0), 2)
        url = f"http://localhost/api/{self.test_id}"
        
        fetched = generator.update_and_fetch_report(url, self.symbol)
        self.assertIsNotNone(fetched)
        
        raw_dump = generator.get_raw_stream_dump()
        self.assertIsNotNone(raw_dump)

if __name__ == "__main__":
    unittest.main()