import unittest
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'skills')))

from market_portfolio_strategy_optimizer import market_portfolio_strategy_optimizer
from market_portfolio_backtester import market_portfolio_backtester
from market_portfolio_performance_analytics import market_portfolio_performance_analytics

class TestEpicPortfolioOptimizationPractical(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_portfolio_file = "test_portfolio_market_data.json"

        portfolio_payload = {
            "portfolio_id": "EPIC-TEST-001",
            "initial_capital": 100000.0,
            "assets": [
                {"ticker": "AAPL", "weight": 0.40, "expected_return": 0.12, "volatility": 0.18},
                {"ticker": "MSFT", "weight": 0.30, "expected_return": 0.14, "volatility": 0.20},
                {"ticker": "GOOGL", "weight": 0.20, "expected_return": 0.11, "volatility": 0.22},
                {"ticker": "BND", "weight": 0.10, "expected_return": 0.05, "volatility": 0.06}
            ],
            "constraints": {
                "min_weight": 0.05,
                "max_weight": 0.50,
                "target_risk": 0.15
            }
        }

        with open(cls.test_portfolio_file, "w", encoding="utf-8") as f:
            json.dump(portfolio_payload, f, indent=4)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_portfolio_file):
            os.remove(cls.test_portfolio_file)

    def test_real_portfolio_optimization_and_rebalancing_workflow(self):
        self.assertTrue(os.path.exists(self.test_portfolio_file), "Файл портфеля должен быть успешно создан на диске.")

        with open(self.test_portfolio_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        print("\n=== [ПРАКТИЧЕСКАЯ ПРОВЕРКА ЭПИКА] Исходный портфель с диска ===")
        print(json.dumps(raw_data, indent=2, ensure_ascii=False))

        optimizer = market_portfolio_strategy_optimizer()
        optimization_result = optimizer.optimize_allocation(raw_data)

        print("\n=== Результат работы market_portfolio_strategy_optimizer ===")
        print(json.dumps(optimization_result, indent=2, ensure_ascii=False))

        self.assertIn("optimized_weights", optimization_result, "Оптимизатор должен вернуть новые веса активов.")
        self.assertIn("expected_portfolio_return", optimization_result)
        self.assertIn("expected_portfolio_volatility", optimization_result)

        backtester = market_portfolio_backtester()
        backtest_report = backtester.run_simulation(optimization_result)

        print("\n=== Результат бэктестинга оптимизированной стратегии (market_portfolio_backtester) ===")
        print(json.dumps(backtest_report, indent=2, ensure_ascii=False))

        analytics = market_portfolio_performance_analytics()
        performance_metrics = analytics.evaluate(backtest_report)

        print("\n=== Финальные метрики производительности (market_portfolio_performance_analytics) ===")
        print(json.dumps(performance_metrics, indent=2, ensure_ascii=False))

        self.assertGreaterEqual(performance_metrics.get("sharpe_ratio", 0.0), 0.0, "Коэффициент Шарпа должен быть рассчитан корректно.")
        print("\nЭпик автоматизированной оптимизации и ребалансировки портфеля успешно прошел реальную проверку!")

if __name__ == "__main__":
    unittest.main()