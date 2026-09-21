import unittest
import os
import tempfile
import uuid
import random
import json

from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge
from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics

class TestMarketPortfolioBacktestEvaluatorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_data_{uuid.uuid4()}.json")
        
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.initial_capital = round(random.uniform(10000.0, 50000.0), 2)
        
        sample_data = {
            self.symbol: [
                {"price": 100.0 + random.uslar if hasattr(random, 'uslar') else 100.0 + random.uniform(-5, 5), "shift": 1},
                {"price": 105.0 + random.uniform(-5, 5), "shift": 2},
                {"price": 102.0 + random.uniform(-5, 5), "shift": 3},
                {"price": 110.0 + random.uniform(-5, 5), "shift": 4}
            ]
        }
        with open(self.storage_file, 'w') as f:
            json.dump(sample_data, f)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_bridge_composition_and_evaluation(self):
        bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        
        self.assertIsInstance(bridge.backtester, MarketPortfolioBacktester)
        self.assertIsInstance(bridge.analytics, PortfolioPerformanceAnalytics)

        strategy_params = {"multiplier": round(random.uniform(1.0, 3.0), 2)}
        evaluation_result = bridge.evaluate_strategy_backtest(self.symbol, self.initial_capital, strategy_params)

        self.assertIsInstance(evaluation_result, dict)
        self.assertIn("backtest_summary", evaluation_result)
        self.assertIn("performance_metrics", evaluation_result)

if __name__ == "__main__":
    unittest.main()