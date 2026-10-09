import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)

class TestMarketPortfolioStressAuditSchedulerHubIntegration(unittest.TestCase):
    def test_audit_cycle_and_dispatch_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        threshold = round(random.uniform(0.01, 0.5), 4)
        storage_target = f"vault_storage_{uuid.uuid4().hex[:8]}.tmp"
        audit_id = f"audit_{uuid.uuid4().hex[:8]}"
        message = f"Stress alert message {uuid.uuid4().hex[:6]}"
        export_format = random.choice(["json", "csv", "xml"])
        audit_data = {"metric": random.randint(100, 1000), "status": "critical"}

        try:
            scheduler = StressAuditSchedulerHub()

            run_res = scheduler.run_audit_cycle(portfolio_id, None, storage_target)
            self.assertIsNotNone(run_res, "Связка со StressAutoRebalanceTrigger при threshold=None должна вернуть результат")

            feed_url = f"http://example.com/feed/{uuid.uuid4().hex[:6]}"
            feed_data = scheduler.get_feed(feed_url)
            self.assertIsInstance(feed_data, bytes)

            dispatch_res = scheduler.dispatch_alert_and_check(audit_id, message, storage_target, export_format)
            self.assertIn("notification", dispatch_res)
            self.assertIn("is_valid", dispatch_res)
            self.assertIn("export_data", dispatch_res)

            process_res = market_portfolio_stress_audit_scheduler_hub_process(
                portfolio_id, threshold, storage_target, audit_data
            )
            self.assertIsInstance(process_res, dict)
            self.assertEqual(process_res.get("vault_storage"), storage_target)
            self.assertIn("trigger_result", process_res)

        finally:
            if os.path.exists(storage_target):
                try:
                    os.remove(storage_target)
                except OSError:
                    pass

if __name__ == "__main__":
    unittest.main()