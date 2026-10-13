import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_health_monitor import (
    MarketPortfolioStressAuditHealthMonitor,
    SubsystemHealthStatus
)
from skills.market_portfolio_stress_audit_summary_vault import (
    MarketPortfolioStressAuditSummaryVault
)

class TestMarketPortfolioStressAuditHealthMonitorIntegration(unittest.TestCase):

    def setUp(self):
        self.vault = MarketPortfolioStressAuditSummaryVault()
        self.subsystem_name = f"test_subsystem_{uuid.uuid4().hex[:8]}"
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[self.subsystem_name])

    def test_full_audit_integration_with_vault(self):
        random_status_choice = random.choice(list(SubsystemHealthStatus))
        random_token = str(uuid.uuid4())

        audit_data = {
            "subsystem": self.subsystem_name,
            "status": random_status_choice.value,
            "token": random_token,
            "error": None
        }

        self.vault.save_summary(self.subsystem_name, audit_data)

        audit_result = self.monitor.run_full_audit()

        self.assertIn("global_status", audit_result)
        self.assertIn("subsystems_details", audit_result)
        self.assertIn(self.subsystem_name, audit_result["subsystems_details"])

        retrieved_vault_data = self.vault.get_summary(self.subsystem_name)
        self.assertEqual(retrieved_vault_data.get("token"), random_token)

    def test_verify_stream_pipeline_with_real_vault_target(self):
        random_endpoint_id = uuid.uuid4().hex
        result = self.monitor.verify_stream_pipeline(f"http://localhost:8000/stream/{random_endpoint_id}")

        self.assertIsInstance(result, dict)
        self.assertIn("is_active", result)
        self.assertIn("bytes_read", result)

if __name__ == "__main__":
    unittest.main()