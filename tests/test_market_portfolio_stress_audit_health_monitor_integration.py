import unittest
import uuid
import random
import string
from skills.market_portfolio_stress_audit_health_monitor import (
    MarketPortfolioStressAuditHealthMonitor,
    SubsystemHealthStatus,
    HealthMonitorExecutionError
)
from skills.db_storage import db_storage

class TestMarketPortfolioStressAuditHealthMonitorIntegration(unittest.TestCase):

    def setUp(self):
        self.random_subsystem_id = f"subsystem_{uuid.uuid4().hex[:8]}"
        self.monitored_subsystems = [
            self.random_subsystem_id,
            "db_storage",
            "market_portfolio_api_gateway"
        ]
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=self.monitored_subsystems)

    def test_run_full_audit_integration(self):
        audit_result = self.monitor.run_full_audit()

        self.assertIn("global_status", audit_result)
        self.assertIn("subsystems_details", audit_result)

        details = audit_result["subsystems_details"]
        self.assertIsInstance(details, dict)

        for sub in self.monitored_subsystems:
            self.assertIn(sub, details)
            sub_info = details[sub]
            self.assertEqual(sub_info["subsystem"], sub)
            self.assertIn(sub_info["status"], list(SubsystemHealthStatus))

    def test_verify_stream_pipeline_with_random_endpoint(self):
        random_path = ''.join(random.choices(string.ascii_lowercase, k=10))
        fake_target = f"http://localhost:8080/nonexistent_stream_{random_path}"

        pipeline_result = self.monitor.verify_stream_pipeline(fake_target)

        self.assertIsInstance(pipeline_result, dict)
        self.assertIn("is_active", pipeline_result)
        self.assertIn("bytes_read", pipeline_result)
        self.assertFalse(pipeline_result["is_active"])
        self.assertEqual(pipeline_result["bytes_read"], 0)

    def test_storage_interaction_health(self):
        storage_instance = db_storage()
        self.assertIsNotNone(storage_instance)

        audit_result = self.monitor.run_full_audit()
        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)

if __name__ == "__main__":
    unittest.main()