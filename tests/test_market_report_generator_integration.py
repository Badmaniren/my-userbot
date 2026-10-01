import unittest
import os
import uuid
import random
from skills.market_report_generator import MarketReportGenerator, generate_market_report
from skills.market_parser import MarketParser
from skills import db_storage

class TestMarketReportGeneratorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_data_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"market_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        
    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_market_report_generator_integration_flow(self):
        random_price_1 = round(random.uniform(10.0, 500.0), 2)
        random_price_2 = round(random.uniform(501.0, 1000.0), 2)

        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, random_price_1)
        parser.fetch_and_store(self.symbol, random_price_2)

        generator = MarketReportGenerator(storage_file=self.storage_file)

        report = generator.generate_symbol_report(self.symbol)
        
        self.assertIsInstance(report, dict)
        self.assertIn("count", report)
        self.assertGreaterEqual(report["count"], 2)
        self.assertIn("min_price", report)
        self.assertIn("max_price", report)
        self.assertEqual(report["min_price"], min(random_price_1, random_price_2))
        self.assertEqual(report["max_price"], max(random_price_1, random_price_2))

        raw_dump = generator.get_raw_stream_dump()
        self.assertIsNotNone(raw_dump)

        func_report = generate_market_report(self.storage_file, self.symbol)
        self.assertIsInstance(func_report, str)
        self.assertIn(self.symbol, func_report)

    def test_update_and_fetch_report_integration(self):
        fallback_url = f"http://localhost/{uuid.uuid4().hex}"
        generator = MarketReportGenerator(storage_file=self.storage_file)

        fetched_price = generator.update_and_fetch_report(fallback_url, self.symbol)
        self.assertIsInstance(fetched_price, float)

        stored_data = generator.get_raw_stream_dump()
        self.assertIsNotNone(stored_data)

if __name__ == "__main__":
    unittest.main()