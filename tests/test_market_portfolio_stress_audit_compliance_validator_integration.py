import unittest
import uuid
import random
import datetime
from skills.market_portfolio_stress_audit_compliance_validator import (
    MarketPortfolioStressAuditComplianceValidator,
    market_portfolio_stress_audit_compliance_validator
)
from skills import market_portfolio_stress_audit_summary_vault
from skills.db_storage import db_storage

class TestMarketPortfolioStressAuditComplianceValidatorIntegration(unittest.TestCase):
    def setUp(self):
        self.validator = MarketPortfolioStressAuditComplianceValidator()
        self.test_audit_id = f"audit-{uuid.uuid4()}"
        self.test_vault_key = f"vault-{uuid.uuid4()}"
        self.random_score = round(random.uniform(10.0, 95.0), 2)
        self.random_drawdown = round(random.uniform(0.05, 0.45), 2)
        self.risk_threshold = 0.20

    def test_validate_audit_compliance_integration(self):
        # Подготавливаем структуру данных через реальное хранилище сводок аудит-стрессов
        audit_payload = {
            "audit_id": self.test_audit_id,
            "max_drawdown": self.random_drawdown,
            "regulatory_status": "COMPLIANT" if self.random_drawdown <= self.risk_threshold else "NON_COMPLIANT",
            "compliance_score": self.random_score
        }

        # Сохраняем во временное хранилище vault для реальной сквозной интеграции
        db_storage(self.test_audit_id, audit_payload)

        # Вызываем метод валидации
        result = self.validator.validate_audit_compliance(self.test_audit_id, self.risk_threshold)

        # Проверяем сквозные данные
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("audit_id"), self.test_audit_id)
        self.assertIn("is_compliant", result)
        self.assertIn("violations", result)

        if self.random_drawdown > self.risk_threshold:
            self.assertFalse(result["is_compliant"])
            self.assertTrue(any(v["metric"] == "max_drawdown" for v in result["violations"]))
        else:
            # Если статус в сгенерированных данных COMPLIANT и лимит не превышен
            if audit_payload["regulatory_status"] == "COMPLIANT":
                self.assertTrue(result["is_compliant"])

    def test_functional_validator_wrapper_integration(self):
        # Проверяем интеграционную функцию-обертку с генерацией случайных параметров
        vault_payload = {
            "audit_id": self.test_audit_id,
            "compliance_score": self.random_score
        }
        db_storage(self.test_vault_key, vault_payload)

        result = market_portfolio_stress_audit_compliance_validator(self.test_vault_key)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("audit_id"), self.test_audit_id)
        self.assertIsInstance(result.get("is_compliant"), bool)

        # Проверяем сохранение результата обратно в db_storage
        persisted_result = db_storage(self.test_vault_key)
        self.assertEqual(persisted_result.get("is_compliant"), result.get("is_compliant"))
        self.assertEqual(persisted_result.get("audit_id"), self.test_audit_id)

    def test_evaluate_single_rule_integration(self):
        rule_def = {
            "metric": "test_metric",
            "max_limit": 50.0
        }
        exceeding_payload = {
            "test_metric": 75.0
        }
        violation = self.validator._evaluate_single_rule(exceeding_payload, rule_def)

        self.assertIsNotNone(violation)
        self.assertEqual(violation.get("metric"), "test_metric")
        self.assertEqual(violation.get("value"), 75.0)
        self.assertEqual(violation.get("max_limit"), 50.0)

if __name__ == "__main__":
    unittest.main()