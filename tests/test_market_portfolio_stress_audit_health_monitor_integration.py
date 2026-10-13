import unittest
import uuid
import random
import time
from skills.market_portfolio_stress_audit_health_monitor import market_portfolio_stress_audit_health_monitor
from skills.market_portfolio_stress_audit_summary_vault import market_portfolio_stress_audit_summary_vault

class TestMarketPortfolioStressAuditHealthMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.health_monitor = market_portfolio_stress_audit_health_monitor()
        self.summary_vault = market_portfolio_stress_audit_summary_vault()
        self.test_session_id = f"session_{uuid.uuid4().hex[:8]}"

    def test_full_audit_health_lifecycle_integration(self):
        # Генерируем случайные входные данные для исключения кэширования и заглушек
        random_audit_id = f"AUDIT-{uuid.uuid4()}"
        random_risk_value = random.uniform(0.001, 0.999)
        random_asset_count = random.randint(1, 1000)

        # 1. Напрямую записываем данные в хранилище (Vault), с которым должен интегрироваться монитор
        audit_payload = {
            "audit_id": random_audit_id,
            "risk_index": random_risk_value,
            "assets_processed": random_asset_count,
            "timestamp": time.time(),
            "integrity_hash": f"hash-{uuid.uuid4()}"
        }

        vault_save_result = self.summary_vault.save_audit_summary(
            audit_id=random_audit_id,
            summary_data=audit_payload
        )

        # Проверяем, что vault действительно сохранил данные (возвращает ID или статус)
        self.assertTrue(vault_save_result)

        # 2. Вызываем монитор здоровья, который должен подтянуть данные из vault БЕЗ моков
        # Ожидаем, что монитор проанализирует целостность данных в vault
        health_status = self.health_monitor.check_audit_integrity(random_audit_id)

        # 3. Проверки реальности интеграции
        self.assertIsNotNone(health_status, "Монитор должен вернуть объект статуса")
        self.assertEqual(health_status.get("audit_id"), random_audit_id, "Монитор вернул некорректный ID аудита")

        # Проверяем, что монитор "увидел" именно те случайные данные, что мы положили в Vault
        self.assertEqual(
            health_status.get("observed_risk"),
            random_risk_value,
            "Монитор не смог считать актуальные данные из summary_vault"
        )

        # 4. Проверка логики принятия решений монитором на основе данных из vault
        if random_risk_value > 0.8:
            self.assertEqual(health_status.get("health_level"), "CRITICAL")
        else:
            self.assertIn(health_status.get("health_level"), ["STABLE", "WARNING"])

    def test_monitor_sync_with_empty_vault_fails_correctly(self):
        # Проверка поведения при отсутствии данных (реальный негативный сценарий интеграции)
        non_existent_id = f"MISSING-{uuid.uuid4()}"

        result = self.health_monitor.check_audit_integrity(non_existent_id)

        # Интеграция должна корректно обработать отсутствие записи в vault
        self.assertEqual(result.get("status"), "NOT_FOUND")
        self.assertFalse(result.get("is_healthy"))

    def test_batch_health_aggregation_from_vault(self):
        # Создаем пачку случайных аудитов
        audit_ids = [f"BATCH-{uuid.uuid4()}" for _ in range(3)]
        for aid in audit_ids:
            self.summary_vault.save_audit_summary(aid, {"val": random.random()})

        # Монитор должен уметь агрегировать данные по списку из хранилища
        batch_report = self.health_monitor.generate_aggregate_health_report(audit_ids)

        self.assertEqual(len(batch_report.get("processed_items", [])), 3)
        for aid in audit_ids:
            self.assertIn(aid, batch_report.get("report_map", {}))

if __name__ == "__main__":
    unittest.main()