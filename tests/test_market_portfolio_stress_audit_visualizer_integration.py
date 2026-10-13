import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer


class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):

    def test_visualizer_integration_text_summary(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        adaptive_score = round(random.uniform(1.0, 100.0), 2)
        
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }

        visualizer = MarketPortfolioStressAuditVisualizer()
        result = visualizer.visualize(payload)

        self.assertIsInstance(result, str)
        self.assertIn(portfolio_id, result)
        self.assertIn(str(adaptive_score), result)
        self.assertIn("Exported to text report successfully", result)

    def test_visualizer_integration_graphical(self):
        report_id = f"rep-{uuid.uuid4()}"
        tail_risk = round(random.uniform(0.01, 0.5), 4)
        stream_data = f"stream-{uuid.uuid4()}"

        payload = {
            "report_id": report_id,
            "format": "graphical",
            "tail_risk_metrics": {"var_95": tail_risk},
            "stream_payload": stream_data
        }

        visualizer = MarketPortfolioStressAuditVisualizer(db_storage=None)
        result = visualizer.visualize(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("tail_risk_metrics"), {"var_95": tail_risk})
        self.assertEqual(result.get("stream_payload"), stream_data)


if __name__ == "__main__":
    unittest.main()