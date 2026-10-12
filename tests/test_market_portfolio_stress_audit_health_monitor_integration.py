import unittest
import uuid
import random
import string
from skills.market_portfolio_stress_audit_health_monitor import (
    MarketPortfolioStressAuditHealthMonitor,
    SubsystemHealthStatus,
    HealthMonitorExecutionError,
    _dummy_subsystem_func
)

class TestMarketPortfolioStressAuditHealthMonitorIntegration(unittest.TestCase):

    def test_full_audit_integration_with_real_subsystems(self):
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=8))
        subsystem_name_1 = f"market_portfolio_monitor_{random_suffix}"
        subsystem_name_2 = f"market_portfolio_scenario_simulator_{random_suffix}"

        subsystems_list = [subsystem_name_1, subsystem_name_2]
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=subsystems_list)

        audit_result = monitor.run_full_audit()

        self.assertIn("global_status", audit_result)
        self.assertIn("subsystems_details", audit_result)
        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)

        details = audit_result["subsystems_details"]
        self.assertIn(subsystem_name_1, details)
        self.assertIn(subsystem_name_2, details)

        self.assertEqual(details[subsystem_name_1]["subsystem"], subsystem_name_1)
        self.assertEqual(details[subsystem_name_1]["status"], SubsystemHealthStatus.HEALTHY)

    def test_verify_stream_pipeline_with_invalid_target(self):
        random_id = uuid.uuid4().hex
        invalid_url = f"http://localhost:11111/{random_id}"

        monitor = MarketPortfolioStressAuditHealthMonitor()
        pipeline_result = monitor.verify_stream_pipeline(invalid_url)

        self.assertIsInstance(pipeline_result, dict)
        self.assertIn("is_active", pipeline_result)
        self.assertIn("bytes_read", pipeline_result)
        self.assertFalse(pipeline_result["is_active"])
        self.assertEqual(pipeline_result["bytes_read"], 0)

    def test_dynamic_module_attribute_fallback(self):
        random_payload_str = uuid.uuid4().hex
        result = _dummy_subsystem_func(random_payload_str)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "ok")
        self.assertEqual(result.get("payload"), random_payload_str)

if __name__ == "__main__":
    unittest.main()