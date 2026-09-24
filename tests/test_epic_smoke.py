import unittest
import os
import json
from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer
from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge
from skills.market_portfolio_stress_reporter import StressReporter


class TestEpicBacktestingAndScenarioAnalysis(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_filename = "test_market_data_epic.json"

        # Создаем реалистичный набор исторических данных по активу "BTC" на диске
        # Согласно правилам: файл с 20-30 строками реалистичных данных
        historical_data = {
            "BTC": [
                {"timestamp": "2023-01-01", "price": 16500.0},
                {"timestamp": "2023-01-02", "price": 16650.0},
                {"timestamp": "2023-01-03", "price": 16800.0},
                {"timestamp": "2023-01-04", "price": 16750.0},
                {"timestamp": "2023-01-05", "price": 16900.0},
                {"timestamp": "2023-01-06", "price": 17100.0},
                {"timestamp": "2023-01-07", "price": 17250.0},
                {"timestamp": "2023-01-08", "price": 17200.0},
                {"timestamp": "2023-01-09", "price": 17400.0},
                {"timestamp": "2023-01-10", "price": 17550.0},
                {"timestamp": "2023-01-11", "price": 17800.0},
                {"timestamp": "2023-01-12", "price": 18100.0},
                {"timestamp": "2023-01-13", "price": 18000.0},
                {"timestamp": "2023-01-14", "price": 18250.0},
                {"timestamp": "2023-01-15", "price": 18500.0},
                {"timestamp": "2023-01-16", "price": 18800.0},
                {"timestamp": "2023-01-17", "price": 18600.0},
                {"timestamp": "2023-01-18", "price": 18400.0},
                {"timestamp": "2023-01-19", "price": 18700.0},
                {"timestamp": "2023-01-20", "price": 19000.0},
                {"timestamp": "2023-01-21", "price": 19200.0},
                {"timestamp": "2023-01-22", "price": 19500.0},
                {"timestamp": "2023-01-23", "price": 19300.0},
                {"timestamp": "2023-01-24", "price": 19600.0},
                {"timestamp": "2023-01-25", "price": 20000.0}
            ]
        }

        with open(cls.test_filename, "w", encoding="utf-8") as f:
            json.dump(historical_data, f, indent=4)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_filename):
            os.remove(cls.test_filename)

    def test_backtester_execution(self):
        print("\n=== ПРАКТИЧЕСКАЯ ПРОВЕРКА: MarketPortfolioBacktester ===")
        backtester = MarketPortfolioBacktester(self.test_filename)
        summary = backtester.get_backtest_summary("BTC")
        print(f"Сводка бэктеста BTC: {summary}")
        self.assertIsNotNone(summary)

        # Прогон симуляции сделок
        trades = backtester.simulate_historical_trades("BTC", 0.5)
        print(f"Симуляция исторических сделок: {trades}")
        self.assertIsNotNone(trades)

    def test_strategy_optimizer_execution(self):
        print("\n=== ПРАКТИЧЕСКАЯ ПРОВЕРКА: PortfolioStrategyOptimizer ===")
        optimizer = PortfolioStrategyOptimizer(self.test_filename)
        opt_result = optimizer.optimize_strategy("BTC", [0.01, 0.02, -0.01], 5.0)
        print(f"Результаты оптимизации стратегии: {opt_result}")
        self.assertIsInstance(opt_result, dict)

        summary = optimizer.get_strategy_summary("BTC")
        print(f"Резюме стратегии: {summary}")
        self.assertIsNotNone(summary)

    def test_stress_reporter_execution(self):
        print("\n=== ПРАКТИЧЕСКАЯ ПРОВЕРКА: StressReporter ===")
        reporter = StressReporter(self.test_filename)
        stress_report = reporter.run_stress_reporting("BTC", [0.05, 0.10, 0.15])
        print(f"Консолидированный профиль стресс-тестирования: {stress_report}")
        self.assertIsNotNone(stress_report)

    def test_backtest_evaluator_bridge_loop(self):
        print("\n=== ПРАКТИЧЕСКАЯ ПРОВЕРКА: MarketPortfolioBacktestEvaluatorBridge (Замкнутый контур) ===")
        bridge = MarketPortfolioBacktestEvaluatorBridge(self.test_filename)
        evaluation = bridge.evaluate_backtest_performance("BTC")
        print(f"Оценка производительности бэктеста через мост: {evaluation}")
        self.assertIsInstance(evaluation, dict)

        comprehensive = bridge.run_comprehensive_evaluation("BTC", 10000.0, {"param": "aggressive"})
        print(f"Комплексная оценка стратегии и рисков: {comprehensive}")
        self.assertIsInstance(comprehensive, dict)
        print("Эпик бэктестинга и сценарного анализа успешно прошел реальную проверку на данных файла!")


if __name__ == "__main__":
    unittest.main()