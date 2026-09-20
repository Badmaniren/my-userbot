import unittest
import os
import uuid
import random
from skills.market_report_generator import MarketReportGenerator, generate_market_report

class TestMarketReportGeneratorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_data_integration"
        os.makedirs(self.test_dir, exist_ok=True)
        self.unique_id = str(uuid.uuid4())[:8]
        self.storage_file = os.path.join(self.test_dir, f"market_data_{self.unique_id}.json")
        self.symbol = f"BTC_{self.unique_id}"
        self.random_price = round(random.uniform(10000.0, 60000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_pipeline_integration_flow(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        
        test_url = f"https://api.example.com/crypto/{self.symbol}"
        fetched_price = generator.update_and_fetch_report(test_url, self.symbol)
        
        self.assertIsNotNone(fetched_price)
        
        raw_data = generator.get_raw_stream_dump()
        self.assertIsNotNone(raw_data)

        report = generator.generate_symbol_report(self.symbol)
        self.assertIsInstance(report, dict)
        
        functional_report = generate_market_report(self.storage_file, self.symbol)
        self.assertIsInstance(functional_report, str)
        self.assertIn(self.symbol, functional_report)

if __name__ == "__main__":
    unittest.main()