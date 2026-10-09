import unittest
import os
import uuid
import json
import random
from skills.market_portfolio_stress_recovery_coordinator_bridge import StressRecoveryCoordinatorBridge

class TestStressRecoveryCoordinatorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.test_db = f"test_storage_{uuid.uuid4().hex}.db"
        self.bridge = StressRecoveryCoordinatorBridge(storage_file=self.test_db)
        self.symbol = f"SYM-{random.randint(1000, 9999)}"
        self.url = "http://localhost:8080/webhook"
        self.telegram_token = f"bot{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.percentage = random.uniform(0.01, 0.5)
        self.shifts = random.randint(1, 10)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_execute_recovery_workflow_integration(self):
        # Проверка создания файла хранилища
        self.assertTrue(os.path.exists(self.test_db), "Storage file should be created")
        
        # Выполнение реального процесса
        result = self.bridge.execute_recovery_workflow(
            self.symbol,
            self.url,
            self.telegram_token,
            self.chat_id,
            self.percentage,
            self.shifts
        )

        # Проверка структуры ответа
        self.assertIn("stress_result", result)
        self.assertIn("recovery_result", result)
        
        # Проверка записи данных в файл
        with open(self.test_db, "r") as f:
            content = f.read()
            self.assertNotEqual(content, "{}", "Storage should contain updated state after execution")

        # Проверка корректности переданных параметров в результат
        self.assertEqual(result["stress_result"].get("symbol"), self.symbol)

    def test_coordinator_bridge_persistence(self):
        # Проверка, что bridge корректно работает с существующим файлом
        new_bridge = StressRecoveryCoordinatorBridge(storage_file=self.test_db)
        self.assertEqual(new_bridge.storage_file, self.test_db)
        
        # Проверка на отсутствие ошибок при повторном вызове
        try:
            new_bridge.execute_recovery_workflow(
                self.symbol, self.url, self.telegram_token, self.chat_id, 0.1, 1
            )
        except Exception as e:
            self.fail(f"Integration failed on persistent storage: {e}")

if __name__ == '__main__':
    unittest.main()