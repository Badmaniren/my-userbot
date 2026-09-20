import unittest
import os
import uuid
import random
from skills.market_portfolio_optimizer import optimize_portfolio_weights
from skills.market_parser import MarketParser
from skills.market_report_generator import MarketReportGenerator

class TestMarketPortfolioOptimizerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = f"test_data_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"storage_{uuid.uuid4().hex}.json")
        self.symbol = f"TICKER_{random.randint(1000, 9999)}"
        self.url = f"http://example.com/market/{self.symbol.lower()}"

        parser = MarketParser(self.storage_file)
        for _ in range(5):
            price = round(random.uniform(10.0, 500.0), 2)
            parser.fetch_and_store(self.symbol, price)

        reporter = MarketReportGenerator(self.storage_file)
        reporter.generate_symbol_report(self.symbol)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_portfolio_optimizer_integration(self):
        result = optimize_portfolio_weights(self.storage_file, self.symbol)

        self.assertIsInstance(result, dict)
        self.assertIn("optimal_weight", result)
        self.assertIn(self.symbol, result.get("optimal_weight", {}))

        weight = result["optimal_weight"][self.symbol]
        self.assertGreaterEqual(weight, 0.0)
        self.assertLessEqual(weight, 1.0)

if __name__ == "__main__":
    unittest.main()