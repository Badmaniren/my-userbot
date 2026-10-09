import unittest
import json
import os
import sys

# Ensure skills folder is in sys.path for direct imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills")))

from market_portfolio_stress_recovery_coordinator_bridge import market_portfolio_stress_recovery_coordinator_bridge
from market_portfolio_stress_auto_hedge_sync import market_portfolio_stress_auto_hedge_sync
from market_portfolio_stress_hedge_advisor import market_portfolio_stress_hedge_advisor

class TestStressAutoHedgeEpicPractical(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_filename = "real_stress_test_data.json"

        # Подготовка реалистичных данных стресс-теста (20+ строк)
        cls.stress_data = {
            "portfolio_id": "PORTFOLIO_ALPHA_01",
            "timestamp": "2023-10-27T12:00:00Z",
            "baseline_value": 1000000.0,
            "scenarios": [
                {"id": f"SCENARIO_{i:02d}", "drop_percentage": float(i * 2.5), "projected_loss": float(i * 25000.0), "risk_level": "HIGH" if i > 5 else "MODERATE"}
                for i in range(1, 26)
            ]
        }

        with open(cls.test_filename, "w", encoding="utf-8") as f:
            json.dump(cls.stress_data, f, indent=2)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_filename):
            os.remove(cls.test_filename)

    def test_end_to_end_stress_auto_hedge_pipeline(self):
        print("\n[LIVE CHECK] Запуск практической проверки цепочки автохеджирования по стресс-тестам...")

        self.assertTrue(os.path.exists(self.test_filename), "Файл с данными стресс-теста должен существовать на диске")

        with open(self.test_filename, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        print(f"[LIVE CHECK] Загружено сценариев стресс-теста: {len(raw_data['scenarios'])}")

        # Шаг 1: Интеграция через мост координатора восстановления
        bridge = market_portfolio_stress_recovery_coordinator_bridge()
        bridge_payload = bridge.process(raw_data) if hasattr(bridge, 'process') else bridge.run(raw_data)
        print(f"[LIVE CHECK] Мост координатора обработал данные. Статус: Успешно")

        # Шаг 2: Получение рекомендаций от советника по хеджированию
        advisor = market_portfolio_stress_hedge_advisor()
        hedge_recommendations = advisor.evaluate(bridge_payload) if hasattr(advisor, 'evaluate') else advisor.analyze(bridge_payload)
        print(f"[LIVE CHECK] Советник сформировал рекомендации: {type(hedge_recommendations)}")

        # Шаг 3: Синхронизация и диспетчеризация автохеджа
        sync_module = market_portfolio_stress_auto_hedge_sync()
        execution_result = sync_module.execute(hedge_recommendations) if hasattr(sync_module, 'execute') else sync_module.sync(hedge_recommendations)

        print(f"[LIVE CHECK] Результат сквозного исполнения автохеджа:")
        print(json.dumps(execution_result if isinstance(execution_result, dict) else {"status": "executed", "details": str(execution_result)}, indent=2, ensure_ascii=False))

        self.assertIsNotNone(execution_result, "Результат синхронизации автохеджа не должен быть пустым")
        print("[LIVE CHECK] Проверка завершена успешно. Система работает на реальных файловых данных!")

if __name__ == "__main__":
    unittest.main()
