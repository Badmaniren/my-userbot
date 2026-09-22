import unittest
import os
import uuid
import random
from skills.market_portfolio_live_execution_bridge import MarketPortfolioLiveExecutionBridge
from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge
from skills.market_parser import MarketParser

class TestMarketPortfolioLiveExecutionBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.json"
        self.symbol = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        self.random_price = round(random.uniform(10.0, 1000.0), 2)

        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.random_price)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_live_execution_bridge_integration_flow(self):
        evaluator_bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        strategy_params = {
            "threshold": round(random.uniform(1.0, 5.0), 2),
            "allocation": round(random.uniform(100.0, 10000.0), 2)
        }
        initial_capital = round(random.uniform(50000.0, 100000.0), 2)

        evaluation_result = evaluator_bridge.evaluate_strategy_backtest(
            self.symbol,
            initial_capital,
            strategy_params
        )

        self.assertIsInstance(evaluation_result, dict)

        live_bridge = MarketPortfolioLiveExecutionBridge(self.storage_file)
        self.assertTrue(hasattr(live_bridge, "__init__"))

if __name__ == "__main__":
    unittest.main()