import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_health_monitor import (
    MarketPortfolioStressAuditHealthMonitor,
    SubsystemHealthStatus,
    HealthMonitorExecutionError
)

class TestMarketPortfolioStressAuditHealthMonitorIntegration(unittest.TestCase):

    def test_full_audit_integration_with_random_subsystems(self):
        random_suffix = uuid.uuid4().hex[:8]
        subsystems_pool = [
            f"db_storage_{random_suffix}",
            f"market_portfolio_api_gateway_{random_suffix}",
            f"market_portfolio_stress_monte_carlo_engine_{random_suffix}",
            f"market_portfolio_ml_feature_builder_{random_suffix}"
        ]

        selected_subsystems = random.sample(subsystems_pool, k=min(3, len(subsystems_pool)))

        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=selected_subsystems)
        audit_result = monitor.run_full_audit()

        self.assertIn("global_status", audit_result)
        self.assertIn("subsystems_details", audit_result)
        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)

        details = audit_result["subsystems_details"]
        self.assertIsInstance(details, dict)

        for sub in selected_subsystems:
            self.assertIn(sub, details)
            sub_detail = details[sub]
            self.assertEqual(sub_detail["subsystem"], sub)
            self.assertEqual(sub_detail["status"], SubsystemHealthStatus.HEALTHY)
            self.assertIsNone(sub_detail["error"])

    def test_verify_stream_pipeline_invalid_target(self):
        random_port = random.randint(10000, 65535)
        unreachable_target = f"http://localhost:{random_port}/stream/pipeline/{uuid.uuid4()}"

        monitor = MarketPortfolioStressAuditHealthMonitor()
        pipeline_status = monitor.verify_stream_pipeline(unreachable_target)

        self.assertIsInstance(pipeline_status, dict)
        self.assertIn("is_active", pipeline_status)
        self.assertIn("bytes_read", pipeline_status)
        self.assertFalse(pipeline_status["is_active"])
        self.assertEqual(pipeline_status["bytes_read"], 0)

if __name__ == "__main__":
    unittest.main()