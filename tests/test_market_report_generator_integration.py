import unittest
import os
import uuid
import random
from skills.market_report_generator import MarketReportGenerator, generate_market_report

class TestMarketReportGeneratorIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_market_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.price = round(random.uniform(10.0, 500.0), 2)
        
        db_content = f'[{{"symbol": "{self.symbol}", "price": {self.price}}}]'
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(db_content)
            
        self.generator = MarketReportGenerator(storage_file=self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_generate_symbol_report_integration(self):
        report = self.generator.generate_symbol_report(self.symbol)
        
        self.assertIsInstance(report, dict)
        self.assertIn("count", report)
        self.assertEqual(report["count"], 1)
        self.assertEqual(report.get("min_price"), self.price)
        self.assertEqual(report.get("max_price"), self.price)
        self.assertTrue(report.get(self.symbol))

    def test_get_raw_stream_dump_integration(self):
        dump = self.generator.get_raw_stream_dump()
        self.assertIsInstance(dump, list)
        self.assertTrue(len(dump) > 0)
        found = False
        for item in dump:
            if isinstance(item, dict) and item.get("symbol") == self.symbol:
                found = True
                self.assertEqual(item.get("price"), self.price)
        self.assertTrue(found)

    def test_generate_market_report_function_integration(self):
        report_str = generate_market_report(self.storage_file, self.symbol)
        self.assertIsInstance(report_str, str)
        self.assertIn(self.symbol, report_str)
        self.assertIn(str(self.price), report_str)

if __name__ == "__main__":
    unittest.main()