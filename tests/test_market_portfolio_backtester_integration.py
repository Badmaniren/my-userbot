import unittest
import os
import uuid
import random
from skills.market_portfolio_backtester import MarketBacktester
from skills.db_storage import MarketParser

class TestMarketPortfolioBacktesterIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_storage_{self.random_suffix}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_price = round(random.uniform(10.0, 1000.0), 2)
        
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.random_price)
        
        self.backtester = MarketBacktester(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_backtester_integration_with_storage(self):
        self.assertTrue(os.path.exists(self.storage_file))
        
        shift_percentage = round(random.uniform(-50.0, 50.0), 2)
        result = self.backtester.run_backtest(self.symbol, [shift_percentage])
        
        self.assertIsInstance(result, dict)
        self.assertIn(self.symbol, result)
        self.assertTrue(len(result) > 0)

if __name__ == "__main__":
    unittest.main()