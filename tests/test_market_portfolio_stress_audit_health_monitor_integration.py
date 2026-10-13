import unittest
import uuid
import random
import string
import os
from skills.market_portfolio_stress_audit_health_monitor import (
    MarketPortfolioStressAuditHealthMonitor,
    SubsystemHealthStatus
)
from skills.market_portfolio_stress_audit_summary_vault import (
    store_audit_summary,
    get_audit_summary
)
from skills.market_portfolio_stress_audit_visualizer import (
    generate_audit_chart
)


class TestMarketPortfolioStressAuditHealthMonitorIntegration(unittest.TestCase):

    def setUp(self):
        self.random_suffix = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.audit_id = f"audit_{uuid.uuid4().hex[:8]}_{self.random_suffix}"
        self.test_subsystems = [f"sub_{uuid.uuid4().hex[:6]}", f"sub_{uuid.uuid4().hex[:6]}"]
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=self.test_subsystems)

    def test_full_audit_and_vault_storage_integration(self):
        audit_result = self.monitor.run_full_audit()

        self.assertIn("global_status", audit_result)
        self.assertIn("subsystems_details", audit_result)
        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)

        for sub in self.test_subsystems:
            self.assertIn(sub, audit_result["subsystems_details"])
            self.assertEqual(audit_result["subsystems_details"][sub]["status"], SubsystemHealthStatus.HEALTHY)

        summary_payload = {
            "audit_id": self.audit_id,
            "global_status": audit_result["global_status"].value,
            "details": audit_result["subsystems_details"],
            "metric_value": random.uniform(10.0, 1000.0)
        }

        stored_id = store_audit_summary(summary_payload)
        self.assertIsNotNone(stored_id)

        retrieved_summary = get_audit_summary(self.audit_id)
        self.assertIsNotNone(retrieved_summary)
        self.assertEqual(retrieved_summary.get("audit_id"), self.audit_id)
        self.assertEqual(retrieved_summary.get("global_status"), SubsystemHealthStatus.HEALTHY.value)
        self.assertEqual(retrieved_summary.get("metric_value"), summary_payload["metric_value"])

    def test_visualizer_integration_with_audit_data(self):
        dummy_metrics = {
            "total_subsystems": len(self.test_subsystems),
            "healthy_count": len(self.test_subsystems),
            "score": random.randint(80, 100)
        }

        chart_result = generate_audit_chart(self.audit_id, dummy_metrics)
        self.assertIsNotNone(chart_result)


if __name__ == "__main__":
    unittest.main()