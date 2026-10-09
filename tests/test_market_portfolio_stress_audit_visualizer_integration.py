import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer


class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def test_visualizer_integration_flow(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        adaptive_score = round(random.uniform(10.0, 99.9), 2)
        tail_risk_metric = round(random.uniform(0.01, 0.99), 4)

        payload_summary = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }

        visualizer = MarketPortfolioStressAuditVisualizer(db_storage=None)
        
        result_summary = visualizer.visualize(payload_summary)
        
        self.assertIsInstance(result_summary, str)
        self.assertIn(portfolio_id, result_summary)
        self.assertIn(str(adaptive_score), result_summary)
        self.assertIn("Exported to text report successfully.", result_summary)

        payload_graphical = {
            "report_id": portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": adaptive_score,
            "tail_risk_metrics": {"var_95": tail_risk_metric},
            "stream_payload": {"active": True}
        }

        result_graphical = visualizer.visualize(payload_graphical)

        self.assertIsInstance(result_graphical, dict)
        self.assertEqual(result_graphical.get("portfolio_id"), portfolio_id)
        self.assertEqual(result_graphical.get("status"), "success")
        self.assertEqual(result_graphical.get("layout"), "graphical")
        self.assertEqual(result_graphical.get("adaptive_risk_score"), adaptive_score)
        self.assertEqual(result_graphical.get("tail_risk_metrics"), {"var_95": tail_risk_metric})
        self.assertEqual(result_graphical.get("stream_payload"), {"active": True})


if __name__ == "__main__":
    unittest.main()