import unittest
import uuid
import random
import os
from skills import market_portfolio_stress_audit_pipeline_bridge as bridge


class TestMarketPortfolioStressAuditPipelineBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.audit_id = f"audit-{uuid.uuid4()}"
        self.storage_target = f"test_storage_{uuid.uuid4()}.json"
        self.format_type = random.choice(["json", "csv", "pdf"])
        self.metrics = {
            "var_95": round(random.uniform(1000.0, 50000.0), 2),
            "max_drawdown": round(random.uniform(0.05, 0.50), 4),
            "stress_score": random.randint(1, 100)
        }
        self.payload = {
            "storage_target": self.storage_target,
            "expected_audit_id": self.audit_id,
            "audit_id": self.audit_id,
            "audit_data": self.metrics,
            "metrics": self.metrics,
            "format": self.format_type
        }

    def tearDown(self):
        if os.path.exists(self.storage_target):
            try:
                os.remove(self.storage_target)
            except OSError:
                pass

    def test_pipeline_bridge_class_initialization_and_visualization(self):
        pipeline_instance = bridge.MarketPortfolioStressAuditPipelineBridge(storage_target=self.storage_target)
        self.assertEqual(pipeline_instance.storage_target, self.storage_target)

        started_id = pipeline_instance.initialize_audit()
        self.assertIsNotNone(started_id)

        vis_result = pipeline_instance.visualize_audit(self.payload)
        self.assertIsNotNone(vis_result)

    def test_run_stress_audit_pipeline_execution(self):
        result = bridge.run_stress_audit_pipeline(self.payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("audit_id"), self.audit_id)
        self.assertEqual(result.get("status"), "success")

    def test_market_portfolio_stress_audit_pipeline_bridge_execution(self):
        result = bridge.market_portfolio_stress_audit_pipeline_bridge(self.payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("audit_id"), self.audit_id)
        self.assertEqual(result.get("result"), "completed")


if __name__ == "__main__":
    unittest.main()