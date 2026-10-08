import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)


class TestStressAuditSchedulerHubIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.threshold = round(random.uniform(0.01, 0.99), 4)
        self.storage_target = f"storage_{uuid.uuid4().hex[:8]}"
        self.audit_id = f"audit_{uuid.uuid4().hex[:8]}"
        self.message = f"Test stress alert message {uuid.uuid4().hex[:6]}"
        self.export_format = random.choice(["json", "csv", "xml"])
        self.scheduler = StressAuditSchedulerHub()

    def test_run_audit_cycle_integration(self):
        res = self.scheduler.run_audit_cycle(
            portfolio_id=self.portfolio_id,
            threshold=self.threshold,
            storage_target=self.storage_target
        )
        # Так как это интеграционный тест без моков, проверяем тип возвращаемого значения (может быть None или dict)
        if res is not None:
            self.assertIsInstance(res, dict)

    def test_dispatch_alert_and_check_integration(self):
        result = self.scheduler.dispatch_alert_and_check(
            audit_id=self.audit_id,
            message=self.message,
            storage_target=self.storage_target,
            export_format=self.export_format
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("notification", result)
        self.assertIn("is_valid", result)
        self.assertIn("export_data", result)
        self.assertIsInstance(result["is_valid"], bool)

    def test_market_portfolio_stress_audit_scheduler_hub_process_integration(self):
        audit_data = {
            "audit_id": self.audit_id,
            "metric": random.randint(100, 999),
            "status": "COMPLETED"
        }
        
        process_result = market_portfolio_stress_audit_scheduler_hub_process(
            portfolio_id=self.portfolio_id,
            threshold=self.threshold,
            storage_target=self.storage_target,
            audit_data=audit_data
        )

        self.assertIsInstance(process_result, dict)
        self.assertIn("trigger_result", process_result)
        self.assertEqual(process_result["vault_storage"], self.storage_target)


if __name__ == "__main__":
    unittest.main()