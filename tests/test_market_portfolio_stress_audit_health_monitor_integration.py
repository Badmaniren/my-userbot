import unittest
import uuid
import random
import string
from skills.market_portfolio_stress_audit_health_monitor import (
    MarketPortfolioStressAuditHealthMonitor,
    SubsystemHealthStatus,
    HealthMonitorExecutionError,
    db_storage,
    market_portfolio_monitor,
    market_portfolio_stress_scenario_pipeline
)

class TestMarketPortfolioStressAuditHealthMonitorIntegration(unittest.TestCase):

    def setUp(self):
        self.random_subsystem_1 = f"subsystem_{uuid.uuid4().hex[:8]}"
        self.random_subsystem_2 = f"subsystem_{uuid.uuid4().hex[:8]}"
        self.subsystems = [self.random_subsystem_1, self.random_subsystem_2]
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=self.subsystems)

    def test_run_full_audit_integration(self):
        audit_result = self.monitor.run_full_audit()
        
        self.assertIn("global_status", audit_result)
        self.assertIn("subsystems_details", audit_result)
        
        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)
        
        details = audit_result["subsystems_details"]
        self.assertIn(self.random_subsystem_1, details)
        self.assertIn(self.random_subsystem_2, details)
        
        sub_detail = details[self.random_subsystem_1]
        self.assertEqual(sub_detail["subsystem"], self.random_subsystem_1)
        self.assertEqual(sub_detail["status"], SubsystemHealthStatus.HEALTHY)

    def test_dynamic_module_getattr_integration(self):
        random_payload_str = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        
        res_db = db_storage(random_payload_str)
        self.assertIsInstance(res_db, dict)
        self.assertEqual(res_db.get("status"), "ok")
        self.assertEqual(res_db.get("payload"), random_payload_str)

        res_monitor = market_portfolio_monitor(random_payload_str)
        self.assertIsInstance(res_monitor, dict)
        self.assertEqual(res_monitor.get("payload"), random_payload_str)

        res_pipeline = market_portfolio_stress_scenario_pipeline(random_payload_str)
        self.assertIsInstance(res_pipeline, dict)
        self.assertEqual(res_pipeline.get("payload"), random_payload_str)

    def test_verify_stream_pipeline_integration(self):
        random_port = random.randint(10000, 65535)
        invalid_target = f"http://127.0.0.1:{random_port}/{uuid.uuid4().hex}"
        
        stream_result = self.monitor.verify_stream_pipeline(invalid_target)
        
        self.assertIsInstance(stream_result, dict)
        self.assertIn("is_active", stream_result)
        self.assertIn("bytes_read", stream_result)
        self.assertFalse(stream_result["is_active"])
        self.assertEqual(stream_result["bytes_read"], 0)

if __name__ == "__main__":
    unittest.main()