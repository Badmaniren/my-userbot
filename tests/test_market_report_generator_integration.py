import unittest
import os
import uuid
import random
from skills.market_report_generator import MarketReportGenerator, generate_market_report

class TestMarketReportGeneratorIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_storage_{self.random_suffix}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        self.test_price = round(random.uniform(10.0, 1000.0), 2)
        
    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_report_pipeline_integration(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        
        raw_dump_initial = generator.get_raw_stream_dump()
        self.assertTrue(raw_dump_initial is None or isinstance(raw_dump_initial, (dict, list)))

        updated_price = generator.update_and_fetch_report("http://localhost:8000/mock", self.symbol)
        self.assertIsNotNone(updated_price)

        symbol_report = generator.generate_symbol_report(self.symbol)
        self.assertIsInstance(symbol_report, dict)
        self.assertIn("count", symbol_report)

        free_report = generate_market_report(self.storage_file, self.symbol)
        self.assertIsInstance(free_report, str)
        self.assertIn(self.symbol, free_report)

if __name__ == "__main__":
    unittest.main()