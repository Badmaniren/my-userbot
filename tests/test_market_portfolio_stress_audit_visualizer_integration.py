import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer, market_portfolio_stress_audit_visualizer

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.adaptive_risk_score = round(random.uniform(1.0, 100.0), 2)
        self.visualizer = MarketPortfolioStressAuditVisualizer(db_storage=None)

    def test_visualize_text_summary_integration(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.adaptive_risk_score,
            "export_to_text_report": True
        }
        
        result_class = self.visualizer.visualize(payload)
        result_func = market_portfolio_stress_audit_visualizer(payload)

        self.assertIsInstance(result_class, str)
        self.assertIsInstance(result_func, str)
        self.assertIn(self.portfolio_id, result_class)
        self.assertIn(str(self.adaptive_risk_score), result_class)
        self.assertIn("Exported to text report successfully.", result_class)
        self.assertEqual(result_class, result_func)

    def test_visualize_graphical_integration(self):
        tail_risk = {"var_95": random.uniform(0.01, 0.05), "cvar_95": random.uniform(0.05, 0.15)}
        payload = {
            "report_id": self.portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": self.adaptive_risk_score,
            "tail_risk_metrics": tail_risk,
            "stream_payload": {"active": True}
        }

        result = self.visualizer.visualize(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), self.adaptive_risk_score)
        self.assertEqual(result.get("tail_risk_metrics"), tail_risk)
        self.assertIsNotNone(result.get("stream_payload"))

    def test_invalid_payload_integration(self):
        random_payload = str(uuid.uuid4())
        result = self.visualizer.visualize(random_payload)
        self.assertEqual(result, random_payload)

if __name__ == "__main__":
    unittest.main()