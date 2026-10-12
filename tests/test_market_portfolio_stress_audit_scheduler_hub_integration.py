import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)
from skills.market_portfolio_stress_auto_rebalance_trigger import StressAutoRebalanceTrigger
from skills.market_portfolio_stress_audit_summary_vault import (
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class TestMarketPortfolioStressAuditSchedulerHubIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.audit_id = f"audit_{uuid.uuid4().hex[:8]}"
        self.threshold = round(random.uniform(0.01, 0.99), 4)
        self.storage_target = f"storage_{uuid.uuid4().hex[:8]}.json"
        self.feed_url = f"https://api.risk-feed.internal/v1/stress/{uuid.uuid4().hex[:6]}"
        self.message = f"Critical stress anomaly detected: {uuid.uuid4().hex[:6]}"
        self.export_format = random.choice(["json", "csv", "xml"])

        self.audit_data = {
            "audit_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "stress_level": self.threshold,
            "timestamp": random.randint(1700000000, 1800000000)
        }

    def tearDown(self):
        if os.path.exists(self.storage_target):
            try:
                os.remove(self.storage_target)
            except OSError:
                pass

    def test_full_stress_audit_scheduler_integration(self):
        scheduler = StressAuditSchedulerHub()

        cycle_result = scheduler.run_audit_cycle(
            portfolio_id=self.portfolio_id,
            threshold=self.threshold,
            storage_target=self.storage_target
        )
        self.assertIsNotNone(cycle_result)

        feed_data = scheduler.get_feed(self.feed_url)
        self.assertIsInstance(feed_data, bytes)

        dispatch_result = scheduler.dispatch_alert_and_check(
            audit_id=self.audit_id,
            message=self.message,
            storage_target=self.storage_target,
            export_format=self.export_format
        )

        self.assertIn("notification", dispatch_result)
        self.assertIn("is_valid", dispatch_result)
        self.assertIn("export_data", dispatch_result)
        self.assertIsInstance(dispatch_result["is_valid"], bool)

        process_result = market_portfolio_stress_audit_scheduler_hub_process(
            portfolio_id=self.portfolio_id,
            threshold=self.threshold,
            storage_target=self.storage_target,
            audit_data=self.audit_data
        )

        self.assertIsInstance(process_result, dict)
        self.assertEqual(process_result["vault_storage"], self.storage_target)
        self.assertIn("trigger_result", process_result)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, self.audit_id)
        self.assertTrue(is_valid)

if __name__ == "__main__":
    unittest.main()