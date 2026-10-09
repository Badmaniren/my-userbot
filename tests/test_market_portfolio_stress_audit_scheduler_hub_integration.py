import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)

class TestStressAuditSchedulerHubIntegration(unittest.TestCase):
    def setUp(self):
        self.scheduler = StressAuditSchedulerHub()
        self.portfolio_id = str(uuid.uuid4())
        self.threshold = random.uniform(0.01, 0.15)
        self.storage_target = f"test_storage_{uuid.uuid4().hex[:8]}.json"
        self.audit_id = str(uuid.uuid4())

    def tearDown(self):
        if os.path.exists(self.storage_target):
            os.remove(self.storage_target)

    def test_full_audit_cycle_integration(self):
        # Проверка цикла аудита без моков
        result = self.scheduler.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)
        
        # Если триггер сработал, проверяем наличие данных в хранилище
        if result is not None:
            self.assertTrue(os.path.exists(self.storage_target))

    def test_dispatch_alert_and_check_flow(self):
        # Проверка сквозного процесса уведомления и валидации
        message = f"Stress alert for {self.portfolio_id}"
        export_format = "json"
        
        response = self.scheduler.dispatch_alert_and_check(
            self.audit_id, 
            message, 
            self.storage_target, 
            export_format
        )
        
        self.assertIn("notification", response)
        self.assertIn("is_valid", response)
        self.assertIn("export_data", response)
        # Валидация должна вернуть bool, даже если файл не создан
        self.assertIsInstance(response["is_valid"], bool)

    def test_scheduler_hub_process_execution(self):
        # Проверка интеграции через основной процесс модуля
        audit_data = {"risk_score": random.random(), "timestamp": uuid.uuid4().hex}
        
        process_result = market_portfolio_stress_audit_scheduler_hub_process(
            self.portfolio_id,
            self.threshold,
            self.storage_target,
            audit_data
        )
        
        self.assertEqual(process_result["vault_storage"], self.storage_target)
        self.assertTrue(os.path.exists(self.storage_target))

    def test_feed_fetching_resilience(self):
        # Проверка обработки внешних фидов (античит: не должно падать при плохом URL)
        bad_url = f"http://invalid-url-{uuid.uuid4()}.local"
        feed = self.scheduler.get_feed(bad_url)
        self.assertEqual(feed, b"")

if __name__ == '__main__':
    unittest.main()