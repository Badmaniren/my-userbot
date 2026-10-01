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
        self.symbol = f"TICK_{random.randint(1000, 9999)}"
        self.test_price = round(random.uniform(10.0, 1000.0), 2)
        
        if hasattr(db_storage, "init_db"):
            try:
                db_storage.init_db(self.storage_file)
            except Exception:
                pass

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except Exception:
                pass

    def test_integration_market_report_pipeline(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.test_price)
        
        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be created by the integration pipeline")

        generator = MarketReportGenerator(self.storage_file)
        symbol_report = generator.generate_symbol_report(self.symbol)
        
        self.assertIn('count', symbol_report)
        self.assertGreater(symbol_report['count'], 0)
        self.assertEqual(symbol_report.get('min_price'), self.test_price)
        self.assertEqual(symbol_report.get('max_price'), self.test_price)
        self.assertTrue(symbol_report.get(self.symbol))

        raw_dump = generator.get_raw_stream_dump()
        self.assertIsNotNone(raw_dump)

        global_report_str = generate_market_report(self.storage_file, self.symbol)
        self.assertIsInstance(global_report_str, str)
        self.assertIn(self.symbol, global_report_str)
        self.assertIn(str(self.test_price), global_report_str)

if __name__ == '__main__':
    unittest.main()