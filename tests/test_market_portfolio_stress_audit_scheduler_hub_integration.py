import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)


class TestMarketPortfolioStressAuditSchedulerHubIntegration(unittest.TestCase):

    def test_audit_scheduler_hub_integration_workflow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        threshold = round(random.uniform(0.01, 0.5), 4)
        storage_target = f"vault_storage_{uuid.uuid4().hex[:8]}"
        audit_id = f"audit_{uuid.uuid4().hex[:8]}"
        message = f"Integration test stress alert message {uuid.uuid4().hex[:6]}"
        export_format = random.choice(["json", "csv", "xml"])
        audit_data = {
            "metrics": {
                "var_95": random.uniform(1000, 50000),
                "max_drawdown": random.uniform(0.05, 0.45)
            },
            "status": "active"
        }

        scheduler = StressAuditSchedulerHub()

        run_res = scheduler.run_audit_cycle(portfolio_id, threshold, storage_target)
        self.assertIsNotNone(run_res)

        feed_url = f"https://api.risk-metrics-provider-{uuid.uuid4().hex[:6]}.internal/feed"
        feed_data = scheduler.get_feed(feed_url)
        self.assertIsInstance(feed_data, bytes)

        dispatch_res = scheduler.dispatch_alert_and_check(audit_id, message, storage_target, export_format)
        self.assertIn("notification", dispatch_res)
        self.assertIn("is_valid", dispatch_res)
        self.assertIn("export_data", dispatch_res)
        self.assertIsInstance(dispatch_res["is_valid"], bool)

        process_res = market_portfolio_stress_audit_scheduler_hub_process(
            portfolio_id, threshold, storage_target, audit_data
        )
        self.assertIn("trigger_result", process_res)
        self.assertEqual(process_res["vault_storage"], storage_target)
        self.assertEqual(process_res["trigger_result"], run_res)


if __name__ == "__main__":
    unittest.main()