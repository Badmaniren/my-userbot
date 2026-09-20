import unittest
import os
import uuid
import random
from skills.market_report_generator import MarketReportGenerator, generate_market_report

class TestMarketReportGeneratorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_data"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"test_db_{uuid.uuid4()}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.test_url = f"https://example.com/market/{uuid.uuid4()}"
        self.report_generator = MarketReportGenerator(storage_file=self.storage_file)

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

    def test_integration_report_and_storage_flow(self):
        random_price = round(random.uniform(10.0, 1000.0), 2)
        
        fetched_price = self.report_generator.update_and_fetch_report(self.test_url, self.symbol)
        
        self.report_generator.parser.fetch_and_store(self.symbol, random_price)
        
        report = self.report_generator.generate_symbol_report(self.symbol)
        
        self.assertIn('count', report)
        self.assertGreaterEqual(report['count'], 1)
        self.assertIn('min_price', report)
        self.assertIn('max_price', report)
        self.assertTrue(report.get(self.symbol))

        raw_dump = self.report_generator.get_raw_stream_dump()
        self.assertIsNotNone(raw_dump)

        legacy_report_string = generate_market_report(self.storage_file, self.symbol)
        self.assertIsInstance(legacy_report_string, str)
        self.assertIn(self.symbol, legacy_report_string)

if __name__ == '__main__':
    unittest.main()