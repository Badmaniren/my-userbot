import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer, market_portfolio_stress_audit_visualizer

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.adaptive_risk_score = round(random.uniform(1.0, 100.0), 2)
        self.visualizer = MarketPortfolioStressAuditVisualizer()

    def test_visualize_text_summary_integration(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.adaptive_risk_score,
            "export_to_text_report": True
        }
        
        result = self.visualizer.visualize(payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(self.portfolio_id, result)
        self.assertIn(str(self.adaptive_risk_score), result)
        self.assertIn("Exported to text report successfully.", result)

    def test_visualize_graphical_format_integration(self):
        tail_metric_val = random.randint(10, 500)
        payload = {
            "report_id": self.portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": self.adaptive_risk_score,
            "tail_risk_metrics": {"var_95": tail_metric_val},
            "stream_payload": {"active": True}
        }
        
        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), self.adaptive_risk_score)
        self.assertEqual(result.get("tail_risk_metrics"), {"var_95": tail_metric_val})
        self.assertEqual(result.get("stream_payload"), {"active": True})

    def test_invalid_payload_handling(self):
        random_string_payload = f"invalid_payload_{uuid.uuid4()}"
        result = market_portfolio_stress_audit_visualizer(random_string_payload)
        
        self.assertIsInstance(result, str)
        self.assertEqual(result, random_string_payload)

if __name__ == "__main__":
    unittest.main()