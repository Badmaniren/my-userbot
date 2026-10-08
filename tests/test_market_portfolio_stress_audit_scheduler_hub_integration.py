import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)
from skills.db_storage import DBStorage

class TestMarketPortfolioStressAuditSchedulerHubIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.threshold = round(random.uniform(0.01, 0.99), 4)
        self.storage_target = f"test_storage_{uuid.uuid4().hex[:8]}"
        self.audit_data = {
            "audit_metric": random.randint(100, 1000),
            "status": "active",
            "score": random.random()
        }
        self.scheduler = StressAuditSchedulerHub()
        self.db = DBStorage()

    def test_run_audit_cycle_and_process(self):
        result = market_portfolio_stress_audit_scheduler_hub_process(
            self.portfolio_id,
            self.threshold,
            self.storage_target,
            self.audit_data
        )
        self.assertIsInstance(result, dict)
        self.assertIn("trigger_result", result)
        self.assertEqual(result["vault_storage"], self.storage_target)

    def test_dispatch_alert_and_check(self):
        audit_id = str(uuid.uuid4())
        message = f"Stress alert message {uuid.uuid4()}"
        export_format = random.choice(["json", "csv", "xml"])

        dispatch_result = self.scheduler.dispatch_alert_and_check(
            audit_id,
            message,
            self.storage_target,
            export_format
        )

        self.assertIsInstance(dispatch_result, dict)
        self.assertIn("notification", dispatch_result)
        self.assertIn("is_valid", dispatch_result)
        self.assertIn("export_data", dispatch_result)
        self.assertIsInstance(dispatch_result["is_valid"], bool)

    def test_get_feed_integration(self):
        feed_url = f"https://api.risk-feed-simulator.internal/v1/stress/{uuid.uuid4()}"
        feed_response = self.scheduler.get_feed(feed_url)
        self.assertIsNotNone(feed_response)

if __name__ == "__main__":
    unittest.main()