import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_health_monitor import market_portfolio_stress_audit_health_monitor
from skills.db_storage import MarketParser
from skills import market_portfolio_collector_agent
from skills import market_portfolio_stress_audit_summary_vault

class IntegrationTestMarketPortfolioStressAuditHealthMonitor(unittest.TestCase):
    def test_health_monitor_integration_flow(self):
        unique_test_id = str(uuid.uuid4())
        test_metric_value = random.uniform(10.5, 999.9)
        test_telemetry_payload = {
            "audit_id": unique_test_id,
            "risk_score": test_metric_value,
            "status": "active"
        }

        parser_instance = MarketParser()
        collector_module = market_portfolio_collector_agent
        vault_module = market_portfolio_stress_audit_summary_vault
        health_monitor_instance = market_portfolio_stress_audit_health_monitor()

        if hasattr(collector_module, "start_new"):
            try:
                collector_module.start_new(test_telemetry_payload)
            except Exception:
                pass

        if hasattr(vault_module, "market_portfolio_stress_audit_summary_vault_process"):
            try:
                vault_module.market_portfolio_stress_audit_summary_vault_process("/tmp/test_audit.json", test_telemetry_payload)
            except Exception:
                pass

        health_status = health_monitor_instance.check_health(
            target_audit_id=unique_test_id,
            expected_min_telemetry=test_metric_value - 1.0
        )

        self.assertIsInstance(health_status, dict)
        self.assertIn("status", health_status)
        self.assertEqual(health_status.get("audit_id"), unique_test_id)
        self.assertTrue(health_status.get("storage_available"))
        self.assertTrue(health_status.get("telemetry_valid"))

        if hasattr(parser_instance, "get"):
            retrieved_data = parser_instance.get(unique_test_id)
            if retrieved_data:
                self.assertEqual(retrieved_data.get("risk_score"), test_metric_value)

if __name__ == "__main__":
    unittest.main()
