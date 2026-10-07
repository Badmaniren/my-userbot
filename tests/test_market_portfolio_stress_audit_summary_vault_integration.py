import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_stress_audit_summary_vault import (
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class TestMarketPortfolioStressAuditSummaryVaultIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.audit_id = str(uuid.uuid4())
        self.portfolio_id = str(uuid.uuid4())
        self.stress_score = round(random.uniform(10.0, 99.9), 2)
        self.risk_factor = random.choice(["HIGH", "MODERATE", "CRITICAL", "LOW"])
        
        self.payload = {
            "audit_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "stress_score": self.stress_score,
            "risk_factor": self.risk_factor,
            "metrics": {
                "var_95": round(random.uniform(1000.0, 50000.0), 2),
                "max_drawdown": round(random.uniform(0.05, 0.50), 4)
            }
        }

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_vault_lifecycle(self):
        storage_path = os.path.join(self.test_dir.name, f"vault_{self.audit_id}.json")
        
        save_result = market_portfolio_stress_audit_summary_vault_process(
            storage_target=storage_path,
            audit_data=self.payload
        )
        
        self.assertIsInstance(save_result, dict)
        self.assertEqual(save_result.get("status"), "saved")
        self.assertEqual(save_result.get("audit_id"), self.audit_id)
        
        self.assertTrue(os.path.exists(storage_path), "Интеграционный тест: Файл хранилища не был создан.")

        is_valid = market_portfolio_stress_audit_summary_vault_validate(
            storage_target=storage_path,
            expected_audit_id=self.audit_id
        )
        self.assertTrue(is_valid, "Интеграционный тест: Валидация сохраненного отчета не прошла.")

        export_result = market_portfolio_stress_audit_summary_vault_export(
            storage_target=storage_path,
            format="json"
        )
        
        self.assertIsInstance(export_result, dict)
        self.assertIn("data", export_result)
        self.assertEqual(export_result["data"]["portfolio_id"], self.portfolio_id)
        self.assertEqual(export_result["data"]["stress_score"], self.stress_score)
        self.assertEqual(export_result["data"]["risk_factor"], self.risk_factor)

if __name__ == "__main__":
    unittest.main()