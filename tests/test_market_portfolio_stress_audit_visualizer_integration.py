import unittest
import uuid
import random

from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer


class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def test_visualizer_integration_text_summary(self):
        portfolio_id = str(uuid.uuid4())
        adaptive_risk_score = round(random.uniform(1.0, 100.0), 2)
        
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_risk_score,
            "export_to_text_report": True
        }
        
        visualizer = MarketPortfolioStressAuditVisualizer(db_storage=None)
        result = visualizer.visualize(payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(portfolio_id, result)
        self.assertIn(str(adaptive_risk_score), result)
        self.assertIn("Exported to text report successfully.", result)

    def test_visualizer_integration_graphical(self):
        report_id = str(uuid.uuid4())
        adaptive_risk_score = round(random.uniform(0.0, 10.0), 4)
        tail_risk_var = round(random.uniform(-50.0, -1.0), 2)
        stream_token = str(uuid.uuid4())
        
        payload = {
            "report_id": report_id,
            "format": "graphical",
            "adaptive_risk_score": adaptive_risk_score,
            "tail_risk_metrics": {"var_95": tail_risk_var},
            "stream_payload": {"token": stream_token}
        }
        
        visualizer = MarketPortfolioStressAuditVisualizer(db_storage="real_db_stub")
        result = visualizer.visualize(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), adaptive_risk_score)
        self.assertEqual(result.get("tail_risk_metrics"), {"var_95": tail_risk_var})
        self.assertEqual(result.get("stream_payload"), {"token": stream_token})


if __name__ == "__main__":
    unittest.main()