import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_stress_audit_risk_telemetry import (
    market_portfolio_stress_audit_risk_telemetry
)
from skills.db_storage import db_storage
from skills.market_portfolio_stress_audit_summary_vault import market_portfolio_stress_audit_summary_vault
from skills.market_portfolio_data_exporter import market_portfolio_data_exporter

class TestMarketPortfolioStressAuditRiskTelemetryIntegration(unittest.TestCase):
    def setUp(self):
        self.test_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.test_audit_id = f"audit_{uuid.uuid4().hex[:8]}"
        self.risk_threshold = round(random.uniform(0.01, 0.99), 4)
        self.telemetry_metric_value = random.randint(100, 9999)

    def test_stress_audit_risk_telemetry_flow(self):
        # 1. Инициализируем хранилище и записываем базовые данные через реальные зависимости без моков
        db_storage.initialize()
        
        vault_payload = {
            "portfolio_id": self.test_portfolio_id,
            "audit_id": self.test_audit_id,
            "risk_score": self.risk_threshold,
            "metric": self.teleny_metric_value if hasattr(self, 'teleny_metric_value') else self.telemetry_metric_value
        }
        
        vault_res = market_portfolio_stress_audit_summary_vault.store_audit_summary(vault_payload)
        self.assertIsNotNone(vault_res, "Vault должен вернуть результат сохранения")

        # 2. Вызываем тестируемый модуль телеметрии стресс-аудита
        telemetry_input = {
            "portfolio_id": self.test_portfolio_id,
            "audit_id": self.test_audit_id,
            "collect_metrics": True
        }
        
        telemetry_output = market_portfolio_stress_audit_risk_telemetry.process_telemetry(telemetry_input)
        
        # Проверяем возврат конкретных случайных ID и параметров
        self.assertIsInstance(telemetry_output, dict)
        self.assertEqual(telemetry_output.get("portfolio_id"), self.test_portfolio_id)
        self.assertEqual(telemetry_output.get("audit_id"), self.test_audit_id)
        self.assertIn("telemetry_id", telemetry_output)

        # 3. Экспортируем данные телеметрии через реальный экспортер
        export_config = {
            "target_format": "json",
            "audit_id": self.test_audit_id,
            "include_risk_telemetry": True
        }
        
        export_result = market_portfolio_data_exporter.export_audit_data(export_config)
        self.assertTrue(export_result.get("success"), "Экспорт телеметрии должен завершиться успешно")
        
        exported_filepath = export_result.get("filepath")
        if exported_filepath:
            self.assertTrue(os.path.exists(exported_filepath), "Файл экспорта телеметрии должен реально существовать на диске")
            with open(exported_filepath, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(self.test_portfolio_id, content)
                self.assertIn(self.test_audit_id, content)

if __name__ == "__main__":
    unittest.main()