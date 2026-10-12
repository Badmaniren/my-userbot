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
from skills.db_storage import save_audit_result, get_audit_result

class TestMarketPortfolioStressAuditHealthMonitorIntegration(unittest.TestCase):

    def test_full_audit_integration_with_real_storage(self):
        subsystem_name = f"subsystem_{uuid.uuid4().hex[:8]}"
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[subsystem_name])

        audit_result = monitor.run_full_audit()

        self.assertIn("global_status", audit_result)
        self.assertIn("subsystems_details", audit_result)
        self.assertIn(subsystem_name, audit_result["subsystems_details"])

        random_metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        random_metric_value = random.randint(100, 9999)
        
        payload = {
            "audit_id": str(uuid.uuid4()),
            "subsystem": subsystem_name,
            "status": audit_result["global_status"].value,
            random_metric_key: random_metric_value
        }

        save_audit_result(payload["audit_id"], payload)
        retrieved = get_audit_result(payload["audit_id"])

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.get("audit_id"), payload["audit_id"])
        self.assertEqual(retrieved.get(random_metric_key), random_metric_value)

    def test_verify_stream_pipeline_strict_validation(self):
        random_port = random.randint(10000, 65535)
        invalid_target = f"http://localhost:{random_port}/{uuid.uuid4().hex}"
        
        monitor = MarketPortfolioStressAuditHealthMonitor()
        
        with self.assertRaises(Exception):
            monitor.verify_stream_pipeline(invalid_target)

if __name__ == "__main__":
    unittest.main()