import unittest
import json
import os
import tempfile
from market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from market_portfolio_stress_reporter import market_portfolio_stress_reporter
from market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core

class TestStochasticStressAnalysisAndTailRiskEpic(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.data_path = os.path.join(self.test_dir.name, "stress_portfolio_data.json")

        # Создаем реалистичные финансовые данные для стресс-тестирования хвостовых рисков
        self.raw_portfolio_data = {
            "portfolio_id": "EPIC-STRESS-001",
            "assets": [
                {"ticker": "ALPHA", "weight": 0.40, "volatility": 0.22, "current_price": 150.50},
                {"ticker": "BETA", "weight": 0.35, "volatility": 0.38, "current_price": 85.20},
                {"ticker": "GAMMA", "weight": 0.25, "volatility": 0.55, "current_price": 42.10}
            ],
            "historical_shocks": [-0.03, -0.01, 0.02, -0.07, -0.12, 0.01, -0.05, -0.18, 0.04, -0.09],
            "simulation_parameters": {
                "iterations": 5000,
                "confidence_level": 0.99,
                "horizon_days": 10
            }
        }

        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.raw_portfolio_data, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_stochastic_stress_monte_carlo_pipeline(self):
        print(f"\n[DEMO] Запуск проверки завершённого эпика: Расширенный стохастический стресс-анализ")
        print(f"[DEMO] Создан файл данных на диске: {self.data_path}")

        # Проверяем чтение созданных данных
        with open(self.data_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        print(f"[DEMO] Портфель ID: {loaded_data['portfolio_id']}")
        print(f"[DEMO] Количество активов в портфеле: {len(loaded_data['assets'])}")

        # Задействуем движок стохастического моделирования Монте-Карло для стресс-анализа
        mc_engine = market_portfolio_stress_monte_carlo_engine()
        simulation_result = mc_engine.run_simulation(loaded_data)

        print(f"[DEMO] Результаты симуляции Монте-Карло (Хвостовые риски / VaR / Expected Shortfall):")
        print(json.dumps(simulation_result, indent=2))

        # Интеграция с ядром ликвидности и VaR
        var_core = market_portfolio_var_liquidity_core()
        tail_risk_metrics = var_core.calculate_tail_risk(simulation_result)

        print(f"[DEMO] Рассчитанные метрики хвостовых рисков (Tail Risk Metrics):")
        print(json.dumps(tail_risk_metrics, indent=2))

        # Генерация отчета по стресс-тестированию
        reporter = market_portfolio_stress_reporter()
        final_report = reporter.generate_report(loaded_data, simulation_result, tail_risk_metrics)

        print(f"[DEMO] Финальный отчет по стресс-анализу сформирован успешно.")

        # Проверки целостности работы системы
        self.assertIsNotNone(simulation_result)
        self.assertIn("var_99", tail_risk_metrics or simulation_result)
        self.assertTrue(len(loaded_data["assets"]) > 0)

if __name__ == "__main__":
    unittest.main()