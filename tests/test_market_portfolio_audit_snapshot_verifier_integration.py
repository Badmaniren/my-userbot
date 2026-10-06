import unittest
import uuid
import random
from skills import market_portfolio_audit_snapshot_verifier
from skills import db_storage

class TestMarketPortfolioAuditSnapshotVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.db = db_storage
        self.verifier = market_portfolio_audit_snapshot_verifier
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.snapshot_id = f"snap_{uuid.uuid4().hex[:8]}"
        self.test_value = round(random.uniform(1000.0, 1000000.0), 2)

    def test_snapshot_verification_workflow(self):
        # Подготовка реальных данных в хранилище без использования моков
        if hasattr(self.db, "save_snapshot") and callable(self.db.save_snapshot):
            self.db.save_snapshot(
                portfolio_id=self.portfolio_id,
                snapshot_id=self.snapshot_id,
                total_value=self.test_value
            )

        # Вызов тестируемого модуля интеграции/верификации
        verification_result = None
        if hasattr(self.verifier, "verify_snapshot") and callable(self.verifier.verify_snapshot):
            verification_result = self.verifier.verify_snapshot(self.snapshot_id)
        elif hasattr(self.verifier, "audit_snapshot") and callable(self.verifier.audit_snapshot):
            verification_result = self.verifier.audit_snapshot(self.snapshot_id)
        elif hasattr(self.verifier, "run") and callable(self.verifier.run):
            verification_result = self.verifier.run(self.snapshot_id)

        # Проверка реального поведения и возврата данных
        self.assertIsNotNone(verification_result, "Модуль не вернул результат верификации снапшота")
        
        if isinstance(verification_result, dict):
            self.assertIn("status", verification_result)
            self.assertEqual(verification_result.get("snapshot_id"), self.snapshot_id)

if __name__ == "__main__":
    unittest.main()