import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer


class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.visualizer = MarketPortfolioStressAuditVisualizer()

    def test_visualize_text_summary_integration(self):
        portfolio_id = str(uuid.uuid4())
        adaptive_score = round(random.uniform(10.0, 99.9), 2)
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }

        result = self.visualizer.visualize(payload)

        self.assertIsInstance(result, str)
        self.assertIn(portfolio_id, result)
        self.assertIn(str(adaptive_score), result)
        self.assertIn("Exported to text report successfully.", result)

    def test_visualize_graphical_format_integration(self):
        report_id = str(uuid.uuid4())
        tail_metric = f"tail_risk_{uuid.uuid4().hex[:6]}"
        stream_val = random.randint(1000, 9999)
        payload = {
            "report_id": report_id,
            "format": "graphical",
            "tail_risk_metrics": tail_metric,
            "stream_payload": stream_val
        }

        result = self.visualizer.visualize(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("tail_risk_metrics"), tail_metric)
        self.assertEqual(result.get("stream_payload"), stream_val)


if __name__ == "__main__":
    unittest.main()