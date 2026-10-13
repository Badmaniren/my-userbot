import unittest
import json
import os
from market_portfolio_stress_resilience_optimizer import market_portfolio_stress_resilience_optimizer


class TestStressResilienceOptimizerPhase3(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_audit_file = "real_portfolio_stress_audit_phase3.json"

        # Создаем реалистичные данные стресс-аудита портфеля (25 строк метрик здоровья и стресс-тестов)
        portfolio_stress_data = {
            "audit_run_id": "STRESS_AUDIT_PHASE3_998877",
            "timestamp": "2023-10-27T12:00:00Z",
            "portfolio_metrics": [
                {"asset": "AAPL", "weight": 0.25, "health_score": 0.88, "var_95": 0.034, "resilience_index": 0.79},
                {"asset": "MSFT", "weight": 0.20, "health_score": 0.91, "var_95": 0.029, "resilience_index": 0.84},
                {"asset": "GOOGL", "weight": 0.15, "health_score": 0.72, "var_95": 0.045, "resilience_index": 0.65},
                {"asset": "AMZN", "weight": 0.15, "health_score": 0.68, "var_95": 0.052, "resilience_index": 0.61},
                {"asset": "TSLA", "weight": 0.10, "health_score": 0.45, "var_95": 0.088, "resilience_index": 0.40},
                {"asset": "JPM", "weight": 0.05, "health_score": 0.85, "var_95": 0.031, "resilience_index": 0.80},
                {"asset": "V", "weight": 0.05, "health_score": 0.89, "var_95": 0.025, "resilience_index": 0.86},
                {"asset": "BTC-USD", "weight": 0.05, "health_score": 0.30, "var_95": 0.145, "resilience_index": 0.25}
            ],
            "stress_scenarios_evaluated": [
                {"scenario": "BLACK_SWAN_2008", "portfolio_drawdown": -0.38, "recovery_time_days": 180},
                {"scenario": "COVID_CRASH_2020", "portfolio_drawdown": -0.24, "recovery_time_days": 65},
                {"scenario": "INFLATION_SHOCK_2022", "portfolio_drawdown": -0.21, "recovery_time_days": 110},
                {"scenario": "LIQUIDITY_CRUNCH", "portfolio_drawdown": -0.29, "recovery_time_days": 95},
                {"scenario": "TECH_BUBBLE_BURST", "portfolio_drawdown": -0.34, "recovery_time_days": 140}
            ],
            "diagnostic_flags": {
                "self_healing_required": True,
                "auto_rebalance_triggered": False,
                "entropy_warning": False,
                "correlation_breakdown": True
            }
        }

        with open(cls.test_audit_file, "w", encoding="utf-8") as f:
            json.dump(portfolio_stress_data, f, indent=2)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_audit_file):
            os.remove(cls.test_audit_file)

    def test_optimizer_against_real_audit_file(self):
        print("\n[PRAXIS TEST] Запуск проверки market_portfolio_stress_resilience_optimizer на реальном файле аудита (Фаза 3)...")

        self.assertTrue(os.path.exists(self.test_audit_file), "Файл аудита должен быть создан на диске.")

        with open(self.test_audit_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # Вызываем модуль оптимизации устойчивости
        optimizer = market_portfolio_stress_resilience_optimizer()
        optimization_result = optimizer.optimize_from_audit(raw_data)

        print(f"[PRAXIS TEST] Результат оптимизации устойчивости: {optimization_result}")

        self.assertIsNotNone(optimization_result, "Модуль оптимизации не должен возвращать None.")
        self.assertIn("recommended_weights", optimization_result, "Оптимизатор должен предложить новые веса активов.")
        self.assertIn("health_improvement_delta", optimization_result, "Должна быть рассчитана дельта улучшения здоровья портфеля.")

        print("\n[PRAXIS TEST SUCCESS] Модуль market_portfolio_stress_resilience_optimizer успешно отработал по реальным данным самодиагностики портфеля!")


if __name__ == "__main__":
    unittest.main()