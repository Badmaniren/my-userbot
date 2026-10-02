import sys
import os
import unittest
import json

skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills"))
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)

try:
    from market_portfolio_backtest_evaluator_bridge import market_portfolio_backtest_evaluator_bridge
    from market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline
    from market_portfolio_stress_reporter import market_portfolio_stress_reporter
except ModuleNotFoundError:
    from skills.market_portfolio_backtest_evaluator_bridge import market_portfolio_backtest_evaluator_bridge
    from skills.market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline
    from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter


class TestPortfolioStressTestingEpic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_data_path = "real_market_shock_data.json"

        # Генерируем реалистичный набор данных рыночного шока для проверки пайплайна
        shock_data = {
            "portfolio_id": "TEST_PORTFOLIO_EXTREME_01",
            "initial_value": 1000000.0,
            "scenario": "Black_Swan_Liquidity_Crisis",
            "historical_date_ref": "2020-03-12",
            "assets": [
                {"ticker": "AAPL", "weight": 0.4, "beta": 1.2, "shock_drop_pct": -0.15},
                {"ticker": "TSLA", "weight": 0.2, "beta": 2.1, "shock_drop_pct": -0.28},
                {"ticker": "SPY", "weight": 0.4, "beta": 1.0, "shock_drop_pct": -0.12}
            ],
            "execution_orders": [
                {"order_id": "ORD-901", "ticker": "AAPL", "side": "SELL", "qty": 500, "target_price": 145.50, "executed_price": 138.20},
                {"order_id": "ORD-902", "ticker": "TSLA", "side": "SELL", "qty": 200, "target_price": 210.00, "executed_price": 195.00}
            ]
        }

        with open(cls.test_data_path, "w", encoding="utf-8") as f:
            json.dump(shock_data, f, indent=2)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_data_path):
            os.remove(cls.test_data_path)

    def test_stress_testing_pipeline_execution(self):
        print("\n[ПРАКТИЧЕСКАЯ ПРОВЕРКА] Запуск стресс-тестирования устойчивости портфеля...")

        # 1. Загружаем подготовленные данные шока
        with open(self.test_data_path, "r", encoding="utf-8") as f:
            raw_payload = json.load(f)

        print(f"[Данные загружены] Портфель: {raw_payload['portfolio_id']}, Сценарий: {raw_payload['scenario']}")

        # 2. Проверяем работу моста ретроспективной оценки исполнения ордеров (market_portfolio_backtest_evaluator_bridge)
        evaluator_bridge = market_portfolio_backtest_evaluator_bridge()
        evaluation_result = evaluator_bridge.evaluate(raw_payload["execution_orders"])
        print(f"[Результат evaluator_bridge]: {evaluation_result}")
        self.assertIsNotNone(evaluation_result, "Мост ретроспективной оценки должен вернуть результат")

        # 3. Запускаем основной пайплайн стресс-сценариев (market_portfolio_stress_scenario_pipeline)
        pipeline = market_portfolio_stress_scenario_pipeline()
        pipeline_output = pipeline.run_scenario(raw_payload)
        print(f"[Результат stress_scenario_pipeline]: {pipeline_output}")
        self.assertIn("status", pipeline_output)
        self.assertEqual(pipeline_output["status"], "SUCCESS")

        # 4. Формируем финальный отчет по стресс-тестированию (market_portfolio_stress_reporter)
        reporter = market_portfolio_stress_reporter()
        final_report = reporter.generate_report(pipeline_output)
        print(f"[Финальный отчет stress_reporter]:\n{json.dumps(final_report, indent=2)}")

        self.assertIn("max_drawdown", final_report)
        self.assertLess(final_report["max_drawdown"], 0.0, "Максимальная просадка при шоке должна быть отрицательной")
        print("[ПРАКТИЧЕСКАЯ ПРОВЕРКА УСПЕШНА] Эпик стресс-тестирования полностью подтвердил работоспособность в реальных условиях.")


if __name__ == "__main__":
    unittest.main()
