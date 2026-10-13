import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_health_monitor import (
    MarketPortfolioStressAuditHealthMonitor,
    SubsystemHealthStatus
)
from skills.db_storage import db_storage
from skills.market_portfolio_stress_audit_summary_vault import market_portfolio_stress_audit_summary_vault

class TestMarketPortfolioStressAuditHealthMonitorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_run_id = str(uuid.uuid4())
        self.subsystems_to_test = ["db_storage", "market_portfolio_stress_audit_summary_vault"]
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=self.subsystems_to_test)

    def test_full_audit_integrity_and_storage_persistence(self):
        # 1. Подготовка: записываем случайные данные в хранилище для проверки свежести
        test_key = f"audit_check_{self.test_run_id}"
        test_value = {"metric": random.random(), "status": "active"}

        db_storage.save(test_key, test_value)
        market_portfolio_stress_audit_summary_vault.store_summary(self.test_run_id, {"integrity_check": True})

        # 2. Выполнение: запуск аудита
        audit_result = self.monitor.run_full_audit()

        # 3. Проверка: целостность структуры
        self.assertIn("global_status", audit_result)
        self.assertIn("subsystems_details", audit_result)
        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)

        # 4. Проверка: наличие данных в деталях аудита для целевых систем
        for sub in self.subsystems_to_test:
            self.assertIn(sub, audit_result["subsystems_details"])
            self.assertEqual(audit_result["subsystems_details"][sub]["subsystem"], sub)

        # 5. Проверка: верификация записи через vault (реальное чтение)
        vault_data = market_portfolio_stress_audit_summary_vault.get_summary(self.test_run_id)
        self.assertIsNotNone(vault_data)
        self.assertTrue(vault_data.get("integrity_check"))

    def test_stream_pipeline_connectivity(self):
        # Проверка реального взаимодействия с API шлюзом, если он доступен
        # Используем случайный ID для имитации запроса к потоку
        target_url = "http://localhost:8080/health"

        result = self.monitor.verify_stream_pipeline(target_url)

        # Проверяем, что метод возвращает структуру, а не падает
        self.assertIsInstance(result, dict)
        self.assertIn("is_active", result)
        self.assertIn("bytes_read", result)

    def tearDown(self):
        # Очистка состояния после теста
        try:
            db_storage.delete(f"audit_check_{self.test_run_id}")
        except Exception:
            pass

if __name__ == '__main__':
    unittest.main()
