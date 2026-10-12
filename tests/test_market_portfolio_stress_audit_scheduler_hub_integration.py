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
        self.threshold = round(random.uniform(0.01, 0.5), 4)
        self.storage_target = f"storage_{uuid.uuid4().hex[:8]}"
        self.audit_id = f"audit_{uuid.uuid4().hex[:8]}"
        self.message = f"msg_{uuid.uuid4().hex[:8]}"
        self.export_format = random.choice(["json", "csv", "xml"])
        self.audit_data = {
            "metric": random.randint(100, 999),
            "status": "active",
            "rand_val": uuid.uuid4().hex
        }
        self.feed_url = f"https://api.risk-feed-{uuid.uuid4().hex[:6]}.io/stress"
        self.scheduler = StressAuditSchedulerHub()

    def test_run_audit_cycle_integration(self):
        res = self.scheduler.run_audit_cycle(
            portfolio_id=self.portfolio_id,
            threshold=self.threshold,
            storage_target=self.storage_target
        )
        self.assertTrue(
            res is None or isinstance(res, (dict, list, str, int, float, bool)),
            "Результат выполнения аудита должен иметь допустимый тип"
        )

    def test_get_feed_integration(self):
        feed_content = self.scheduler.get_feed(self.feed_url)
        self.assertIsInstance(
            feed_content, bytes,
            "Лента внешнего стресс-теста должна возвращать байты без подавления критических сбоев"
        )

    def test_dispatch_alert_and_check_strict(self):
        result = self.scheduler.dispatch_alert_and_check(
            audit_id=self.audit_id,
            message=self.message,
            storage_target=self.storage_target,
            export_format=self.export_format
        )
        self.assertIn("notification", result)
        self.assertIn("is_valid", result)
        self.assertIn("export_data", result)
        self.assertIsInstance(result["is_valid"], bool)

    def test_scheduler_hub_process_pipeline(self):
        pipeline_output = market_portfolio_stress_audit_scheduler_hub_process(
            portfolio_id=self.portfolio_id,
            threshold=self.threshold,
            storage_target=self.storage_target,
            audit_data=self.audit_data
        )
        self.assertIsInstance(pipeline_output, dict)
        self.assertIn("trigger_result", pipeline_output)
        self.assertEqual(pipeline_output["vault_storage"], self.storage_target)


if __name__ == "__main__":
    unittest.main()