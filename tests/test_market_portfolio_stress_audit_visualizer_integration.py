import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer


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
        result = self.visualizer.visualize(payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(self.portfolio_id, result)
        self.assertIn(str(self.adaptive_risk_score), result)
        self.assertIn("Exported to text report successfully.", result)

    def test_visualize_graphical_format_integration(self):
        tail_risk = {"var_95": random.uniform(-0.5, -0.1), "cvar_95": random.uniform(-0.8, -0.3)}
        stream_data = {"status_code": random.choice([200, 201]), "packet_id": str(uuid.uuid4())}
        
        payload = {
            "report_id": self.portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": self.adaptive_risk_score,
            "tail_risk_metrics": tail_risk,
            "stream_payload": stream_data
        }
        result = self.visualizer.visualize(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), self.adaptive_risk_score)
        self.assertEqual(result.get("tail_risk_metrics"), tail_risk)
        self.assertEqual(result.get("stream_payload"), stream_data)

    def test_visualize_invalid_payload_handling(self):
        random_payload = str(uuid.uuid4())
        result = self.visualizer.visualize(random_payload)
        self.assertEqual(result, random_payload)


if __name__ == "__main__":
    unittest.main()