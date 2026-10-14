import unittest
import uuid
import random
import string
from skills.market_portfolio_stress_audit_health_monitor import (
    MarketPortfolioStressAuditHealthMonitor,
    SubsystemHealthStatus,
    HealthMonitorExecutionError,
    StorageUnreachableError
)

class TestMarketPortfolioStressAuditHealthMonitorIntegration(unittest.TestCase):

    def setUp(self):
        self.random_subsystem_name = f"subsystem_{uuid.uuid4().hex[:8]}"
        self.random_subsystems_pool = [
            self.random_subsystem_name,
            f"market_parser_{uuid.uuid4().hex[:4]}",
            f"db_storage_{uuid.uuid4().hex[:4]}"
        ]
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=self.random_subsystems_pool)

    def test_run_full_audit_integration(self):
        audit_result = self.monitor.run_full_audit()

        self.assertIn("global_status", audit_result)
        self.assertIn("subsystems_details", audit_result)

        global_status = audit_result["global_status"]
        self.assertIsInstance(global_status, SubsystemHealthStatus)

        details = audit_result["subsystems_details"]
        self.assertIsInstance(details, dict)

        for sub_name in self.random_subsystems_pool:
            self.assertIn(sub_name, details)
            sub_info = details[sub_name]
            self.assertEqual(sub_info["subsystem"], sub_name)
            self.assertIn("status", sub_info)
            self.assertIn("token", sub_info)
            self.assertIn("error", sub_info)

    def test_verify_stream_pipeline_integration(self):
        random_target_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        target_url = f"http://127.0.0.1:1/invalid_stream_{random_target_id}"

        stream_result = self.monitor.verify_stream_pipeline(target_url)

        self.assertIn("is_active", stream_result)
        self.assertIn("bytes_read", stream_result)
        self.assertIsInstance(stream_result["is_active"], bool)
        self.assertIsInstance(stream_result["bytes_read"], int)
        self.assertFalse(stream_result["is_active"])
        self.assertEqual(stream_result["bytes_read"], 0)

    def test_subsystem_error_propagation(self):
        broken_monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[f"fail_sub_{uuid.uuid4().hex[:6]}"])

        def mock_probe_fail(name):
            raise StorageUnreachableError("Storage is down for maintenance")

        broken_monitor._probe_subsystem = mock_probe_fail

        with self.assertRaises(StorageUnreachableError):
            broken_monitor.run_full_audit()

if __name__ == "__main__":
    unittest.main()