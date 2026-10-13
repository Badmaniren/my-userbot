import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_health_monitor import MarketPortfolioStressAuditHealthMonitor, SubsystemHealthStatus
from skills.market_portfolio_stress_audit_summary_vault import MarketPortfolioStressAuditSummaryVault

class TestMarketPortfolioStressAuditIntegration(unittest.TestCase):
    def setUp(self):
        self.vault = MarketPortfolioStressAuditSummaryVault()
        self.monitor = MarketPortfolioStressAuditHealthMonitor(
            subsystems=["market_portfolio_stress_audit_summary_vault"],
            summary_vault=self.vault
        )
        self.test_id = str(uuid.uuid4())
        self.test_payload = {"audit_id": self.test_id, "score": random.uniform(0, 100), "status": "HEALTHY"}

    def test_health_monitor_vault_integration(self):
        # 1. Запись данных в реальный Vault
        write_result = self.vault.store_audit_data(self.test_id, self.test_payload)
        self.assertTrue(write_result, "Vault failed to store data during integration test")

        # 2. Запуск аудита монитором
        audit_report = self.monitor.run_full_audit()

        # 3. Проверка целостности
        self.assertEqual(audit_report["global_status"], SubsystemHealthStatus.HEALTHY)
        self.assertIn("market_portfolio_stress_audit_summary_vault", audit_report["subsystems_details"])

        # 4. Верификация данных через чтение из Vault
        retrieved_data = self.vault.get_audit_data(self.test_id)
        self.assertEqual(retrieved_data["audit_id"], self.test_id)
        self.assertEqual(retrieved_data["score"], self.test_payload["score"])

    def test_stream_pipeline_connectivity(self):
        # Проверка реального сетевого взаимодействия через pipeline
        # Используем валидный эндпоинт, если доступен, или проверяем обработку ошибок
        target = "http://localhost:8080/health"
        result = self.monitor.verify_stream_pipeline(target)

        # Ожидаем корректный словарь ответа, даже если сервис недоступен (is_active: False)
        self.assertIsInstance(result["is_active"], bool)
        self.assertIsInstance(result["bytes_read"], int)

if __name__ == "__main__":
    unittest.main()
