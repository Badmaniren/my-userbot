import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer


class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.adaptive_score = round(random.uniform(10.0, 95.5), 2)
        self.tail_risk_metrics = {
            "var_95": round(random.uniform(-0.15, -0.01), 4),
            "cvar_99": round(random.uniform(-0.25, -0.05), 4)
        }
        self.stream_payload = {
            "stream_id": str(uuid.uuid4()),
            "active": random.choice([True, False])
        }
        self.visualizer = MarketPortfolioStressAuditVisualizer(
            db_storage="mock_db_connection"
        )

    def test_visualize_text_summary_integration(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.adaptive_score,
            "export_to_text_report": True
        }
        result = self.visualizer.visualize(payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(self.portfolio_id, result)
        self.assertIn(str(self.adaptive_score), result)
        self.assertIn("Exported to text report successfully.", result)

    def test_visualize_graphical_dashboard_integration(self):
        payload = {
            "report_id": self.portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": self.adaptive_score,
            "tail_risk_metrics": self.tail_risk_metrics,
            "stream_payload": self.stream_payload
        }
        result = self.visualizer.visualize(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), self.adaptive_score)
        self.assertEqual(result.get("tail_risk_metrics"), self.tail_risk_metrics)
        self.assertEqual(result.get("stream_payload"), self.stream_payload)


if __name__ == "__main__":
    unittest.main()