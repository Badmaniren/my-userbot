import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer


class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def test_visualize_integration_text_summary_flow(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        adaptive_risk_score = round(random.uniform(10.0, 99.9), 2)
        
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_risk_score,
            "export_to_text_report": True
        }
        
        visualizer = MarketPortfolioStressAuditVisualizer()
        result = visualizer.visualize(payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(portfolio_id, result)
        self.assertIn(str(adaptive_risk_score), result)
        self.assertIn("Exported to text report successfully.", result)

    def test_visualize_integration_graphical_flow(self):
        report_id = f"rep-{uuid.uuid4()}"
        adaptive_risk_score = round(random.uniform(1.0, 50.0), 2)
        tail_risk_metric = round(random.uniform(0.01, 0.99), 4)
        stream_token = f"stream-{uuid.uuid4()}"
        
        payload = {
            "report_id": report_id,
            "format": "graphical",
            "adaptive_risk_score": adaptive_risk_score,
            "tail_risk_metrics": {"var_95": tail_risk_metric},
            "stream_payload": stream_token
        }
        
        visualizer = MarketPortfolioStressAuditVisualizer(db_storage=object())
        result = visualizer.visualize(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), adaptive_risk_score)
        self.assertEqual(result.get("tail_risk_metrics"), {"var_95": tail_risk_metric})
        self.assertEqual(result.get("stream_payload"), stream_token)


if __name__ == "__main__":
    unittest.main()