import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer
from skills.market_portfolio_stress_audit_exporter_v2 import market_portfolio_stress_audit_exporter_v2

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.adaptive_risk_score = round(random.uniform(1.0, 100.0), 2)
        self.tail_risk_metrics = {"var_99": random.uniform(-0.5, -0.05), "cvar_99": random.uniform(-0.8, -0.1)}
        self.visualizer = MarketPortfolioStressAuditVisualizer(
            market_portfolio_stress_audit_exporter_v2=market_portfolio_stress_audit_exporter_v2
        )

    def test_visualizer_text_summary_integration(self):
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
        self.assertIn("Exported to text report successfully", result)

    def test_visualizer_graphical_format_integration(self):
        payload = {
            "report_id": self.portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": self.adaptive_risk_score,
            "tail_risk_metrics": self.tail_risk_metrics,
            "stream_payload": {"status": "active", "node": random.randint(1, 10)}
        }
        
        result = self.visualizer.visualize(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), self.adaptive_risk_score)
        self.assertEqual(result.get("tail_risk_metrics"), self.tail_risk_metrics)
        self.assertIn("stream_payload", result)

    def test_visualizer_edge_case_invalid_payload(self):
        random_string_payload = f"invalid_payload_{uuid.uuid4()}"
        result = self.visualizer.visualize(random_string_payload)
        self.assertEqual(result, random_string_payload)

if __name__ == "__main__":
    unittest.main()