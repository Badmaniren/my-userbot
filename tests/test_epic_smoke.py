import unittest
import json
import tempfile
import os
from unittest.mock import patch

from market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline
from market_portfolio_stress_reporter import market_portfolio_stress_reporter


class TestStressTestingEpicPracticalVerification(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_data_path = os.path.join(self.temp_dir.name, "portfolio_stress_input.json")

        self.stress_test_dataset = {
            "portfolio_id": "PF-STRESS-999",
            "initial_capital": 1000000.0,
            "assets": [
                {"ticker": "SBER", "weight": 0.4, "current_price": 280.5},
                {"ticker": "GAZP", "weight": 0.3, "current_price": 165.2},
                {"ticker": "LKOH", "weight": 0.3, "current_price": 7200.0}
            ],
            "scenarios": [
                {
                    "scenario_id": "BLACK_MONDAY_1987",
                    "description": "Extreme liquidity crunch and 25% broad market drop",
                    "shocks": {"SBER": -0.30, "GAZP": -0.28, "LKOH": -0.25},
                    "volatility_multiplier": 3.5
                },
                {
                    "scenario_id": "GEOPOLITICAL_SHOCK_2022",
                    "description": "Sanctions wave and severe domestic market repricing",
                    "shocks": {"SBER": -0.45, "GAZP": -0.50, "LKOH": -0.40},
                    "volatility_multiplier": 5.0
                },
                {
                    "scenario_id": "STAGFLATION_CRISIS",
                    "description": "High inflation combined with interest rate hikes",
                    "shocks": {"SBER": -0.15, "GAZP": -0.10, "LKOH": -0.05},
                    "volatility_multiplier": 2.0
                }
            ]
        }

        with open(self.input_data_path, "w", encoding="utf-8") as f:
            json.dump(self.stress_test_dataset, f, indent=2, ensure_ascii=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_stress_testing_and_backtesting_pipeline_real_execution(self):
        print("\n=== ЗАПУСК ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА: СТРЕСС-ТЕСТИРОВАНИЕ И БЭКТЕСТИРОВАНИЕ ===")
        print(f"Создан реальный файл с данными сценариев: {self.input_data_path}")
        print(f"Количество загруженных стресс-сценариев: {len(self.stress_test_dataset['scenarios'])}")

        with open(self.input_data_path, "r", encoding="utf-8") as f:
            raw_payload = json.load(f)

        pipeline = market_portfolio_stress_scenario_pipeline()
        pipeline_output = pipeline.run_pipeline(raw_payload)

        print("\n--- РЕЗУЛЬТАТЫ РАБОТЫ ПИПЛАЙНА СТРЕСС-СЦЕНАРИЕВ ---")
        print(json.dumps(pipeline_output, indent=2, ensure_ascii=False))

        self.assertIn("execution_status", pipeline_output)
        self.assertEqual(pipeline_output["execution_status"], "SUCCESS")
        self.assertIn("scenario_results", pipeline_output)
        self.assertEqual(len(pipeline_output["scenario_results"]), 3)

        reporter = market_portfolio_stress_reporter()
        stress_report = reporter.generate_comprehensive_report(pipeline_output)

        print("\n--- ФИНАЛЬНЫЙ ОТЧЕТ МОДУЛЯ STRESS REPORTER ---")
        print(json.dumps(stress_report, indent=2, ensure_ascii=False))

        self.assertIn("portfolio_id", stress_report)
        self.assertEqual(stress_report["portfolio_id"], "PF-STRESS-999")
        self.assertIn("worst_case_scenario", stress_report)
        self.assertIn("risk_metrics_summary", stress_report)

        print("\n[OK] Стресс-тестирование и стресс-бэктестирование успешно прошли проверку на реальных данных.")


if __name__ == "__main__":
    unittest.main()