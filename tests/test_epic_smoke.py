import unittest
import json
import os
import random
from datetime import datetime

# Импорт модулей системы
from market_portfolio_audit_compliance_hub import ComplianceHub
from market_portfolio_stress_monte_carlo_engine import MonteCarloEngine
from market_portfolio_stress_reporter import StressReporter

class TestPortfolioAuditEpicCompletion(unittest.TestCase):
    """
    Практическая проверка завершенного эпика: Аудит соответствия и хвостовые риски.
    Цель: Проверить сквозную работу от симуляции Монте-Карло до генерации отчета
    без использования заглушек.
    """

    @classmethod
    def setUpClass(cls):
        # Подготовка реальных данных портфеля для стресс-тестирования
        cls.test_portfolio_data = {
            "assets": ["AAPL", "TSLA", "BTC", "GOLD", "SPY"],
            "weights": [0.2, 0.2, 0.1, 0.2, 0.3],
            "initial_value": 1000000.0,
            "volatility_profile": [0.15, 0.45, 0.80, 0.10, 0.12]
        }
        cls.output_file = "audit_stress_test_result.json"

    def test_end_to_end_audit_pipeline(self):
        print("\n--- ЗАПУСК ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА ---")

        # 1. Инициализация расчетного ядра (Monte Carlo)
        engine = MonteCarloEngine(iterations=1000)
        print(f"[1/3] Запуск симуляции Монте-Карло для {len(self.test_portfolio_data['assets'])} активов...")

        simulation_results = engine.run_simulation(self.test_portfolio_data)
        self.assertIn("var_99", simulation_results, "Симулятор не вернул Value-at-Risk")
        print(f"Результат симуляции: VaR(99%) = {simulation_results['var_99']:.2f}")

        # 2. Проверка соответствия через Compliance Hub
        hub = ComplianceHub()
        print("[2/3] Проверка соответствия регуляторным требованиям...")

        compliance_status = hub.verify_portfolio(self.test_portfolio_data, simulation_results)
        self.assertTrue(compliance_status['is_compliant'], f"Портфель не прошел аудит: {compliance_status.get('reason')}")
        print(f"Статус аудита: {'СООТВЕТСТВУЕТ' if compliance_status['is_compliant'] else 'НАРУШЕНИЕ'}")

        # 3. Генерация отчета
        reporter = StressReporter()
        print("[3/3] Генерация финального отчета...")

        report_data = {
            "timestamp": datetime.now().isoformat(),
            "audit_result": compliance_status,
            "metrics": simulation_results
        }

        report_path = reporter.generate(report_data, self.output_file)

        # Проверка записи файла
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, 'r') as f:
            saved_data = json.load(f)
            print(f"Файл отчета успешно создан: {report_path}")
            print(f"Содержимое отчета (фрагмент): {json.dumps(saved_data['metrics'], indent=2)}")

    def tearDown(self):
        # Очистка артефактов
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
            print("\n--- ПРОВЕРКА ЗАВЕРШЕНА, АРТЕФАКТЫ УДАЛЕНЫ ---")

if __name__ == '__main__':
    unittest.main()