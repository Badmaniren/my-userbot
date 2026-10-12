import unittest
import uuid
import random
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from skills.market_portfolio_stress_audit_health_monitor import (
    MarketPortfolioStressAuditHealthMonitor,
    SubsystemHealthStatus,
    HealthMonitorExecutionError,
    StorageUnreachableError
)


class TestMarketPortfolioStressAuditHealthMonitorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_subsystems = [
            f"market_portfolio_monitor_{uuid.uuid4().hex[:8]}",
            f"market_portfolio_stress_scenario_pipeline_{uuid.uuid4().hex[:8]}",
            f"market_portfolio_api_gateway_{uuid.uuid4().hex[:8]}"
        ]
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=self.test_subsystems)

    def test_run_full_audit_integration(self):
        audit_result = self.monitor.run_full_audit()

        self.assertIn("global_status", audit_result)
        self.assertIn("subsystems_details", audit_result)

        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)

        details = audit_result["subsystems_details"]
        self.assertEqual(len(details), len(self.test_subsystems))

        for sub_name in self.test_subsystems:
            self.assertIn(sub_name, details)
            sub_info = details[sub_name]
            self.assertEqual(sub_info["subsystem"], sub_name)
            self.assertEqual(sub_info["status"], SubsystemHealthStatus.HEALTHY)
            self.assertIsNone(sub_info["token"])
            self.assertIsNone(sub_info["error"])

    def test_verify_stream_pipeline_integration(self):
        random_port = random.randint(10000, 65535)
        non_routable_target = f"http://127.0.0.1:{random_port}/stream/{uuid.uuid4()}"

        stream_result = self.monitor.verify_stream_pipeline(non_routable_target)

        self.assertIn("is_active", stream_result)
        self.assertIn("bytes_read", stream_result)
        self.assertFalse(stream_result["is_active"])
        self.assertEqual(stream_result["bytes_read"], 0)


if __name__ == "__main__":
    unittest.main()