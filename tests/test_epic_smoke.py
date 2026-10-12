import unittest
import os
import json
from skills.market_portfolio_stress_audit_health_monitor import market_portfolio_stress_audit_health_monitor
from skills.market_portfolio_stress_audit_summary_vault import market_portfolio_stress_audit_summary_vault
from skills.market_portfolio_stress_audit_visualizer import market_portfolio_stress_audit_visualizer

class TestStressAuditReliabilityAndSelfDiagnosis(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.vault_filename = "test_stress_audit_summary_vault.json"

        # Создаем реалистичные диагностические метрики здоровья компонентов стресс-аудита
        cls.raw_telemetry_data = {
            "audit_session_id": "STRESS_AUDIT_202X_Q4_FIN",
            "timestamp": "202X-10-15T14:30:00Z",
            "subsystems": {
                "market_portfolio_stress_scenario_matrix_evaluator": {
                    "status": "HEALTHY",
                    "latency_ms": 45.2,
                    "scenarios_evaluated": 128,
                    "error_rate": 0.0
                },
                "market_portfolio_stress_monte_carlo_engine": {
                    "status": "HEALTHY",
                    "latency_ms": 112.8,
                    "iterations": 10000,
                    "error_rate": 0.0
                },
                "market_portfolio_stress_ml_volatility_forecaster_v2": {
                    "status": "WARNING",
                    "latency_ms": 310.5,
                    "model_drift_detected": True,
                    "error_rate": 0.012
                },
                "market_portfolio_stress_audit_health_monitor": {
                    "status": "HEALTHY",
                    "latency_ms": 12.1,
                    "self_diagnostics_passed": True,
                    "error_rate": 0.0
                }
            },
            "overall_health_score": 96.5,
            "circuit_breaker_triggered": False
        }

        with open(cls.vault_filename, "w", encoding="utf-8") as f:
            json.dump(cls.raw_telemetry_data, f, indent=2, ensure_ascii=False)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.vault_filename):
            os.remove(cls.vault_filename)

    def test_health_monitor_self_diagnosis(self):
        print("\n--- Запуск тестов market_portfolio_stress_audit_health_monitor ---")
        monitor = market_portfolio_stress_audit_health_monitor()

        # Проверяем диагностику подсистем на основе созданных данных
        diagnosis_result = monitor.evaluate_subsystems(self.raw_telemetry_data["subsystems"])

        print(f"Результат самодиагностики монитора здоровья: {diagnosis_result}")
        self.assertIsNotNone(diagnosis_result)
        self.assertIn("overall_status", diagnosis_result)
        print(f"Статус здоровья системы: {diagnosis_result.get('overall_status', 'UNKNOWN')}")

    def test_summary_vault_ingestion(self):
        print("\n--- Запуск тестов market_portfolio_stress_audit_summary_vault ---")
        vault = market_portfolio_stress_audit_summary_vault(storage_path=self.vault_filename)

        # Загружаем и проверяем валидацию хранилища сводок
        loaded_summary = vault.load_summary()
        print(f"Загружено из summary vault: {loaded_summary}")

        self.assertEqual(loaded_summary["audit_session_id"], "STRESS_AUDIT_202X_Q4_FIN")
        self.assertIn("market_portfolio_stress_ml_volatility_forecaster_v2", loaded_summary["subsystems"])

    def test_visualizer_contour_closure(self):
        print("\n--- Запуск тестов market_portfolio_stress_audit_visualizer (Замыкание контура) ---")
        visualizer = market_portfolio_stress_audit_visualizer()

        # Агрегируем диагностические метрики и фиксируем в summary vault
        visualization_output = visualizer.aggregate_and_render(self.raw_telemetry_data)

        print(f"Рендер визуализатора метрик здоровья:\n{visualization_output}")
        self.assertIsNotNone(visualization_output)

        # Проверяем, что контур самодиагностики замкнулся успешно
        closed_loop_status = visualizer.verify_loop_closure(self.raw_telemetry_data)
        print(f"Статус замкнутого контура самодиагностики: {closed_loop_status}")
        self.assertTrue(closed_loop_status)

if __name__ == "__main__":
    unittest.main()