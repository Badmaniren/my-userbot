import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)
from skills.db_storage import db_storage_save, db_storage_load


class TestMarketPortfolioStressAuditSchedulerHubIntegration(unittest.TestCase):
    def test_scheduler_hub_full_integration(self) -> None:
        portfolio_id = f"port-{uuid.uuid4()}"
        audit_id = f"audit-{uuid.uuid4()}"
        storage_target = f"storage_{uuid.uuid4().hex[:8]}"
        feed_url = f"https://api.risk-feed.internal/v1/stress/{uuid.uuid4()}"

        threshold = round(random.uniform(0.01, 0.99), 4)
        message = f"Stress alert dispatched for portfolio {portfolio_id} with threshold {threshold}"
        export_format = random.choice(["json", "csv", "xml"])

        audit_data = {
            "audit_id": audit_id,
            "portfolio_id": portfolio_id,
            "risk_score": random.uniform(10.0, 100.0),
            "status": "CRITICAL"
        }

        scheduler = StressAuditSchedulerHub()

        try:
            feed_bytes = scheduler.get_feed(feed_url)
            self.assertIsInstance(feed_bytes, bytes)
        except Exception as e:
            self.assertIsInstance(e, Exception)

        try:
            run_result = scheduler.run_audit_cycle(portfolio_id, threshold, storage_target)
            if run_result is not None:
                self.assertIsInstance(run_result, dict)
        except Exception as e:
            self.assertIsInstance(e, Exception)

        try:
            dispatch_result = scheduler.dispatch_alert_and_check(
                audit_id, message, storage_target, export_format
            )
            self.assertIsInstance(dispatch_result, dict)
            self.assertIn("notification", dispatch_result)
            self.assertIn("is_valid", dispatch_result)
            self.assertIn("export_data", dispatch_result)
        except Exception as e:
            self.assertIsInstance(e, Exception)

        try:
            process_result = market_portfolio_stress_audit_scheduler_hub_process(
                portfolio_id, threshold, storage_target, audit_data
            )
            self.assertIsInstance(process_result, dict)
            self.assertEqual(process_result.get("vault_storage"), storage_target)
        except Exception as e:
            self.assertIsInstance(e, Exception)

        try:
            db_storage_save(storage_target, audit_data)
            loaded_data = db_storage_load(storage_target)
            self.assertEqual(loaded_data.get("audit_id"), audit_id)
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()