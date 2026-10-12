import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)
from skills.db_storage import db_storage_save, db_storage_get

class TestMarketPortfolioStressAuditSchedulerHubIntegration(unittest.TestCase):
    def test_audit_scheduler_hub_integration_flow(self):
        portfolio_id = str(uuid.uuid4())
        threshold = round(random.uniform(0.01, 0.99), 4)
        storage_target = f"test_vault_{uuid.uuid4().hex[:8]}"
        audit_data = {
            "audit_metric": random.randint(100, 999),
            "status": "CRITICAL_STRESS",
            "token": str(uuid.uuid4())
        }
        audit_id = f"audit_{uuid.uuid4().hex[:6]}"
        message = f"Stress alert message {random.randint(1, 1000)}"
        export_format = "json"

        db_storage_save(storage_target, {"initial": True})

        scheduler = StressAuditSchedulerHub()

        feed_url = f"https://api.stress-feed-{uuid.uuid4().hex[:4]}.local/v1/metrics"
        feed_result = scheduler.get_feed(feed_url)
        self.assertIsInstance(feed_result, bytes)

        dispatch_res = scheduler.dispatch_alert_and_check(audit_id, message, storage_target, export_format)
        self.assertIn("notification", dispatch_res)
        self.assertIn("is_valid", dispatch_res)
        self.assertIn("export_data", dispatch_res)

        process_res = market_portfolio_stress_audit_scheduler_hub_process(
            portfolio_id, threshold, storage_target, audit_data
        )
        self.assertIn("trigger_result", process_res)
        self.assertEqual(process_res["vault_storage"], storage_target)

        stored_data = db_storage_get(storage_target)
        self.assertIsNotNone(stored_data)

if __name__ == "__main__":
    unittest.main()