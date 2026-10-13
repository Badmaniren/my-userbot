import unittest
import os
import json
import uuid
import random
import shutil
from skills.market_portfolio_stress_audit_summary_vault import (
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class TestMarketPortfolioStressAuditSummaryVault(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_vault_{uuid.uuid4().hex}"
        self.file_path = os.path.join(self.test_dir, f"audit_{uuid.uuid4().hex}.json")
        self.audit_id = str(uuid.uuid4())
        self.test_data = {
            "audit_id": self.audit_id,
            "stress_score": random.uniform(0, 100),
            "timestamp": random.randint(1600000000, 1700000000),
            "portfolio_id": f"PF-{random.randint(1000, 9999)}"
        }

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_integration_vault_lifecycle(self):
        # 1. Проверка процесса сохранения (Integration: File System)
        result = market_portfolio_stress_audit_summary_vault_process(self.file_path, self.test_data)
        
        self.assertEqual(result["status"], "saved")
        self.assertEqual(result["audit_id"], self.audit_id)
        self.assertTrue(os.path.exists(self.file_path), "Файл аудита не был создан на диске.")

        # 2. Проверка валидации (Integration: Data Integrity)
        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.file_path, self.audit_id)
        self.assertTrue(is_valid, "Валидация файла не прошла успешно.")

        # 3. Проверка экспорта (Integration: Data Retrieval)
        exported = market_portfolio_stress_audit_summary_vault_export(self.file_path)
        self.assertEqual(exported["format"], "json")
        self.assertEqual(exported["data"]["audit_id"], self.audit_id)
        self.assertEqual(exported["data"]["stress_score"], self.test_data["stress_score"])

    def test_invalid_data_handling(self):
        # Проверка обработки некорректных данных
        with self.assertRaises(TypeError):
            market_portfolio_stress_audit_summary_vault_process(self.file_path, "not_a_dict")

    def test_file_not_found_export(self):
        # Проверка поведения при отсутствии файла
        with self.assertRaises(FileNotFoundError):
            market_portfolio_stress_audit_summary_vault_export("non_existent_file.json")

if __name__ == "__main__":
    unittest.main()