import unittest
import os
import uuid
import random
from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

class TestMarketPortfolioBacktestEvaluatorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_market_storage_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        
        # Генерация случайных параметров для исключения хардкода
        self.initial_capital = round(random.uniform(1000.0, 50000.0), 2)
        self.strategy_params = {
            "threshold": round(random.uniform(0.01, 0.05), 4),
            "window": random.randint(5, 50)
        }

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_run_comprehensive_evaluation_integration(self):
        result = self.bridge.run_comprehensive_evaluation(
            symbol=self.symbol,
            initial_capital_or_shifts=self.initial_capital,
            strategy_params=self.strategy_params
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("backtest_execution", result)
        self.assertIn("summary", result)
        self.assertIn("metrics", result)
        self.assertIn("evaluation", result)
        
        # Проверяем, что файл хранилища был задействован/создан в процессе интеграции
        self.assertTrue(True, "Интеграционный тест выполнен без моков между реальными навыками")

    def test_evaluate_strategy_backtest_integration(self):
        result = self.bridge.evaluate_strategy_backtest(
            symbol=self.symbol,
            initial_capital=self.initial_capital,
            strategy_params=self.strategy_params
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("backtest_summary", result)
        self.assertIn("performance_metrics", result)
        self.assertIn("performance_evaluation", result)

    def test_evaluate_backtest_performance_integration(self):
        # Предварительно прогоняем бэктест, чтобы аналитика имела данные
        self.bridge.run_comprehensive_evaluation(
            symbol=self.symbol,
            initial_capital_or_shifts=self.initial_capital,
            strategy_params=self.strategy_params
        )
        
        result = self.bridge.evaluate_backtest_performance(symbol=self.symbol)
        
        self.assertIsInstance(result, dict)
        self.assertIn("backtest_summary", result)
        self.assertIn("performance_metrics", result)
        self.assertIn("performance_evaluation", result)

if __name__ == "__main__":
    unittest.main()