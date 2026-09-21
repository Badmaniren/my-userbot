import os
import unittest
import uuid
import random
from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

class TestMarketPortfolioBacktestEvaluatorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_storage_{self.unique_id}.json"
        self.symbol = f"SYM_{self.unique_id}"
        
        # Заполняем тестовое хранилище минимальными данными, необходимыми для работы бэктестера и аналитики
        import json
        initial_data = {
            self.symbol: [
                {"price": 100.0 + random.random() * 10, "timestamp": "2023-01-01"},
                {"price": 105.0 + random.random() * 10, "timestamp": "2023-01-02"},
                {"price": 110.0 + random.random() * 10, "timestamp": "2023-01-03"},
                {"price": 108.0 + random.random() * 10, "timestamp": "2023-01-04"},
                {"price": 115.0 + random.random() * 10, "timestamp": "2023-01-05"}
            ]
        }
        with open(self.storage_file, "w") as f:
            json.dump(initial_data, f)
            
        self.bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_evaluate_backtest_performance_integration(self):
        result = self.bridge.evaluate_backtest_performance(self.symbol)
        
        self.assertIsInstance(result, dict)
        self.assertIn("backtest_summary", result)
        self.assertIn("performance_metrics", result)
        self.assertIn("performance_evaluation", result)

    def test_run_comprehensive_evaluation_integration(self):
        initial_capital = round(1000.0 + random.random() * 500, 2)
        strategy_params = {"threshold": round(random.random(), 2)}
        
        result = self.bridge.run_comprehensive_evaluation(self.symbol, initial_capital, strategy_params)
        
        self.assertIsInstance(result, dict)
        self.assertIn("backtest_execution", result)
        self.assertIn("summary", result)
        self.assertIn("metrics", result)
        self.assertIn("evaluation", result)

    def test_evaluate_strategy_backtest_integration(self):
        initial_capital = round(5000.0 + random.random() * 1000, 2)
        strategy_params = {"risk_tolerance": round(random.random(), 2)}
        
        result = self.bridge.evaluate_strategy_backtest(self.symbol, initial_capital, strategy_params)
        
        self.assertIsInstance(result, dict)
        self.assertIn("backtest_summary", result)
        self.assertIn("performance_metrics", result)
        self.assertIn("performance_evaluation", result)

if __name__ == "__main__":
    unittest.main()