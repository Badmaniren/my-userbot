import unittest
import uuid
import random
import string
from skills.market_portfolio_stress_audit_health_monitor import (
    MarketPortfolioStressAuditHealthMonitor,
    SubsystemHealthStatus,
    market_portfolio_stress_audit_visualizer,
    db_storage
)

class TestMarketPortfolioStressAuditHealthMonitorIntegration(unittest.TestCase):

    def test_full_audit_and_visualizer_pipeline(self):
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        test_subsystem_name = f"subsystem_{uuid.uuid4()}_{random_suffix}"

        subsystems_list = [
            test_subsystem_name,
            "market_portfolio_stress_audit_visualizer",
            "db_storage"
        ]

        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=subsystems_list)

        audit_result = monitor.run_full_audit()

        self.assertIn("global_status", audit_result)
        self.assertIn("subsystems_details", audit_result)

        details = audit_result["subsystems_details"]
        self.assertIn(test_subsystem_name, details)
        self.assertEqual(details[test_subsystem_name]["status"], SubsystemHealthStatus.HEALTHY)

        visualizer_func = market_portfolio_stress_audit_visualizer
        random_payload_id = str(uuid.uuid4())
        visualizer_response = visualizer_func({"audit_id": random_payload_id, "status": audit_result["global_status"].value})

        self.assertEqual(visualizer_response.get("status"), "ok")
        self.assertEqual(visualizer_response.get("payload")["audit_id"], random_payload_id)

        db_func = db_storage
        db_response = db_func({"target": test_subsystem_name, "check_token": random_suffix})
        self.assertEqual(db_response.get("status"), "ok")
        self.assertEqual(db_response.get("payload")["check_token"], random_suffix)

if __name__ == "__main__":
    unittest.main()