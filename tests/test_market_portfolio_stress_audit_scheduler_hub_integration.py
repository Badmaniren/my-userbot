import unittest
import uuid
import random
import os
import json
from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)

class TestStressAuditSchedulerHubIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.threshold = random.uniform(0.01, 0.15)
        self.storage_target = f"test_vault_{uuid.uuid4().hex}.json"
        self.audit_data = {"risk_score": random.random(), "timestamp": "2023-10-27T10:00:00Z"}
        self.hub = StressAuditSchedulerHub()

    def tearDown(self):
        if os.path.exists(self.storage_target):
            os.remove(self.storage_target)

    def test_full_audit_cycle_integration(self):
        # 1. Проверка процесса через hub_process
        result = market_portfolio_stress_audit_scheduler_hub_process(
            self.portfolio_id,
            self.threshold,
            self.storage_target,
            self.audit_data
        )
        
        self.assertIn("trigger_result", result)
        self.assertEqual(result["vault_storage"], self.storage_target)

        # Проверка записи в "хранилище" (файл должен существовать после процесса)
        self.assertTrue(os.path.exists(self.storage_target))

    def test_dispatch_alert_and_check_flow(self):
        audit_id = str(uuid.uuid4())
        message = f"Stress alert for {self.portfolio_id} with value {random.random()}"
        
        # Выполнение диспетчеризации
        response = self.hub.dispatch_alert_and_check(
            audit_id,
            message,
            self.storage_target,
            "json"
        )

        # Проверка структуры ответа
        self.assertIsInstance(response, dict)
        self.assertIn("notification", response)
        self.assertIn("is_valid", response)
        self.assertIn("export_data", response)

    def test_feed_fetching_resilience(self):
        # Тест на обработку некорректного URL (должен вернуть пустые байты согласно логике)
        invalid_url = f"http://invalid-url-{uuid.uuid4()}.local"
        feed = self.hub.get_feed(invalid_url)
        self.assertEqual(feed, b"")

    def test_data_integrity_in_vault(self):
        # Проверка целостности данных при прохождении через scheduler
        test_data = {"id": str(uuid.uuid4()), "val": random.randint(1, 1000)}

        # Имитация цикла аудита
        self.hub.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)

        # Проверка, что vault принял данные
        with open(self.storage_target, 'r') as f:
            content = f.read()
            self.assertTrue(len(content) > 0)

if __name__ == '__main__':
    unittest.main()