import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)


class TestStressAuditSchedulerHubIntegration(unittest.TestCase):

    def test_audit_scheduler_hub_integration_workflow(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        threshold = round(random.uniform(0.01, 0.5), 4)
        storage_target = f"storage_vault_{uuid.uuid4().hex[:8]}"
        audit_data = {
            "audit_run_id": str(uuid.uuid4()),
            "status": "COMPLETED",
            "metrics": {
                "max_drawdown": random.randint(10, 50),
                "risk_score": random.random()
            }
        }

        feed_url = f"https://api.risk-feed-provider-{uuid.uuid4().hex[:6]}.io/stress"
        audit_id = f"audit-{uuid.uuid4()}"
        message = f"Critical stress alert event {uuid.uuid4()}"
        export_format = random.choice(["json", "csv", "xml"])

        scheduler = StressAuditSchedulerHub()

        run_result = scheduler.run_audit_cycle(portfolio_id, threshold, storage_target)

        feed_data = scheduler.get_feed(feed_url)
        self.assertIsNotNone(feed_data)

        dispatch_res = scheduler.dispatch_alert_and_check(audit_id, message, storage_target, export_format)

        self.assertIn("notification", dispatch_res)
        self.assertIn("is_valid", dispatch_res)
        self.assertIn("export_data", dispatch_res)

        process_result = market_portfolio_stress_audit_scheduler_hub_process(
            portfolio_id, threshold, storage_target, audit_data
        )

        self.assertIn("trigger_result", process_result)
        self.assertEqual(process_result["vault_storage"], storage_target)


if __name__ == "__main__":
    unittest.main()