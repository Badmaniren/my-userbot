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
from skills.db_storage import DBStorage

class TestMarketPortfolioStressAuditHealthMonitorIntegration(unittest.TestCase):

    def setUp(self) -> None:
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.subsystem_name = f"test_subsystem_{random_suffix}_{uuid.uuid4().hex[:6]}"
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[self.subsystem_name])
        self.db = DBStorage()

    def test_full_audit_integration_workflow(self) -> None:
        audit_result = self.monitor.run_full_audit()
        
        self.assertIn("global_status", audit_result)
        self.assertIn("subsystems_details", audit_result)
        
        global_status = audit_result["global_status"]
        self.assertIsInstance(global_status, SubsystemHealthStatus)
        
        details = audit_result["subsystems_details"]
        self.assertIn(self.subsystem_name, details)
        
        sub_detail = details[self.subsystem_name]
        self.assertEqual(sub_detail["subsystem"], self.subsystem_name)
        self.assertEqual(sub_detail["status"], SubsystemHealthStatus.HEALTHY)

    def test_verify_stream_pipeline_with_random_target(self) -> None:
        random_port = random.randint(10000, 65535)
        random_path = ''.join(random.choices(string.ascii_letters, k=10))
        target_url = f"http://127.0.0.1:{random_port}/{random_path}"
        
        stream_result = self.monitor.verify_stream_pipeline(target_url)
        
        self.assertIn("is_active", stream_result)
        self.assertIn("bytes_read", stream_result)
        self.assertIsInstance(stream_result["is_active"], bool)
        self.assertIsInstance(stream_result["bytes_read"], int)
        self.assertFalse(stream_result["is_active"])
        self.assertEqual(stream_result["bytes_read"], 0)

    def test_db_storage_integration_with_monitor(self) -> None:
        self.assertIsNotNone(self.monitor.db)
        self.assertIsInstance(self.monitor.db, DBStorage)

        test_key = f"health_monitor_key_{uuid.uuid4().hex}"
        test_val = f"val_{random.randint(1000, 9999)}"

        if hasattr(self.monitor.db, "set"):
            self.monitor.db.set(test_key, test_val)
            if hasattr(self.monitor.db, "get"):
                retrieved = self.monitor.db.get(test_key)
                self.assertEqual(retrieved, test_val)

if __name__ == "__main__":
    unittest.main()