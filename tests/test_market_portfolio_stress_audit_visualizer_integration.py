import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def test_visualizer_integration_text_summary(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        adaptive_score = round(random.uniform(1.0, 100.0), 2)
        
        visualizer = MarketPortfolioStressAuditVisualizer()
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }
        
        result = visualizer.visualize(payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(portfolio_id, result)
        self.assertIn(str(adaptive_score), result)
        self.assertIn("Exported to text report successfully.", result)

    def test_visualizer_integration_graphical(self):
        report_id = f"rep-{uuid.uuid4()}"
        adaptive_score = round(random.uniform(0.1, 50.0), 4)
        tail_risk_metrics = {"var_95": random.random(), "cvar_95": random.random()}
        stream_payload = {"status_code": random.randint(200, 500)}
        
        visualizer = MarketPortfolioStressAuditVisualizer()
        payload = {
            "report_id": report_id,
            "format": "graphical",
            "adaptive_risk_score": adaptive_score,
            "tail_risk_metrics": tail_risk_metrics,
            "stream_payload": stream_payload
        }
        
        result = visualizer.visualize(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), adaptive_score)
        self.assertEqual(result.get("tail_risk_metrics"), tail_risk_metrics)
        self.assertEqual(result.get("stream_payload"), stream_payload)

if __name__ == "__main__":
    unittest.main()