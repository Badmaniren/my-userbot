import unittest
import os
import uuid
import random
from skills.market_portfolio_websocket_feed import MarketParser
from skills.db_storage import MarketParser as DBMarketParser
from skills.market_portfolio_collector_agent import MarketParser as CollectorMarketParser
from skills.market_portfolio_stress_reporter import StressReporter
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestMarketPortfolioWebsocketFeedIntegration(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_storage_{self.random_suffix}.json"
        self.symbol = f"TICK_{uuid.uuid4().hex[:4].upper()}"
        self.initial_price = round(random.uniform(100.0, 1500.0), 2)
        self.shift_value = round(random.uniform(1.0, 10.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_websocket_feed_integration_pipeline(self):
        ws_parser = MarketParser(self.storage_file)
        db_parser = DBMarketParser(self.storage_file)
        collector = CollectorMarketParser(self.storage_file)

        collector.fetch_and_store(self.symbol, self.initial_price)

        loaded_data = db_parser.load_data(self.storage_file)
        self.assertIsNotNone(loaded_data)

        stress_reporter = StressReporter(self.storage_file)
        stress_result = stress_reporter.run_stress_reporting(self.symbol, [self.shift_value])

        optimizer = PortfolioStrategyOptimizer(self.storage_file)
        summary = optimizer.get_strategy_summary(self.symbol)

        self.assertTrue(os.path.exists(self.storage_file))
        self.assertIsInstance(summary, (dict, type(None)))

if __name__ == '__main__':
    unittest.main()