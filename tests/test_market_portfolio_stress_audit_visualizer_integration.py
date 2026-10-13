import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.visualizer_class = MarketPortfolioStressAuditVisualizer
        self.visualizer_func = market_portfolio_stress_audit_visualizer

    def test_visualizer_integration_text_summary(self):
        portfolio_uuid = str(uuid.uuid4())
        random_score = round(random.uniform(1.0, 100.0), 2)
        
        payload = {
            "portfolio_id": portfolio_uuid,
            "format": "text_summary",
            "adaptive_risk_score": random_score,
            "export_to_text_report": True
        }

        instance = self.visualizer_class(db_storage=None)
        result_from_instance = instance.visualize(payload)
        result_from_func = self.visualizer_func(payload)

        self.assertIsInstance(result_from_instance, str)
        self.assertIsInstance(result_from_func, str)
        self.assertIn(portfolio_uuid, result_from_instance)
        self.assertIn(str(random_score), result_from_instance)
        self.assertIn("Exported to text report successfully.", result_from_instance)
        self.assertEqual(result_from_instance, result_from_func)

    def test_visualizer_integration_graphical(self):
        report_uuid = f"rep_{uuid.uuid4().hex[:8]}"
        random_score = round(random.uniform(0.0, 1.0), 4)
        tail_metric_val = random.randint(10, 500)
        stream_val = f"stream_{uuid.uuid4().hex[:6]}"

        payload = {
            "report_id": report_uuid,
            "format": "graphical",
            "adaptive_risk_score": random_score,
            "tail_risk_metrics": {"var_99": tail_metric_val},
            "stream_payload": stream_val
        }

        instance = self.visualizer_class()
        res = instance.visualize(payload)

        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), report_uuid)
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("layout"), "graphical")
        self.assertEqual(res.get("adaptive_risk_score"), random_score)
        self.assertEqual(res.get("tail_risk_metrics"), {"var_99": tail_metric_val})
        self.assertEqual(res.get("stream_payload"), stream_val)

    def test_visualizer_fallback_primitive(self):
        random_primitive = random.randint(-10000, 10000)
        res = self.visualizer_func(random_primitive)
        self.assertEqual(res, str(random_primitive))

if __name__ == "__main__":
    unittest.main()