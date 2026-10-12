import unittest
import uuid
import random
import os
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
        self.test_subsystems = [
            f"db_storage_{uuid.uuid4().hex[:8]}",
            f"market_portfolio_monitor_{uuid.uuid4().hex[:8]}",
            f"market_portfolio_stress_scenario_pipeline_{uuid.uuid4().hex[:8]}"
        ]
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=self.test_subsystems)

    def test_run_full_audit_real_execution(self):
        audit_result = self.monitor.run_full_audit()
        
        self.assertIn("global_status", audit_result)
        self.assertIn("subsystems_details", audit_result)
        
        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)
        
        details = audit_result["subsystems_details"]
        for sub in self.test_subsystems:
            self.assertIn(sub, details)
            self.assertEqual(details[sub]["subsystem"], sub)
            self.assertEqual(details[sub]["status"], SubsystemHealthStatus.HEALTHY)

    def test_dynamic_module_attributes_integration(self):
        random_payload = {
            "test_id": str(uuid.uuid4()),
            "metric_value": random.uniform(10.0, 1000.0)
        }
        
        db_result = db_storage(random_payload)
        self.assertEqual(db_result["status"], "ok")
        self.assertEqual(db_result["payload"]["test_id"], random_payload["test_id"])
        self.assertEqual(db_result["payload"]["metric_value"], random_payload["metric_value"])

        monitor_result = market_portfolio_monitor(random_payload)
        self.assertEqual(monitor_result["status"], "ok")
        self.assertEqual(monitor_result["payload"], random_payload)

        pipeline_result = market_portfolio_stress_scenario_pipeline(random_payload)
        self.assertEqual(pipeline_result["status"], "ok")

    def test_verify_stream_pipeline_invalid_target(self):
        random_port = random.randint(10000, 65535)
        invalid_target = f"http://localhost:{random_port}/{uuid.uuid4().hex}"
        
        stream_status = self.monitor.verify_stream_pipeline(invalid_target)
        
        self.assertIn("is_active", stream_status)
        self.assertIn("bytes_read", stream_status)
        self.assertFalse(stream_status["is_active"])
        self.assertEqual(stream_status["bytes_read"], 0)

if __name__ == "__main__":
    unittest.main()