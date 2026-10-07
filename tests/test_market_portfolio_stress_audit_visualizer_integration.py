import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer


class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.db_mock = {"storage_status": "active"}
        self.visualizer = MarketPortfolioStressAuditVisualizer(db_storage=self.db_mock)

    def test_visualize_text_summary_integration(self):
        portfolio_id = str(uuid.uuid4())
        adaptive_score = round(random.uniform(1.0, 100.0), 2)
        
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
        report_id = f"rep-{uuid.uuid4()}"
        tail_risk = {"var_95": random.uniform(-0.5, -0.1), "cvar_95": random.uniform(-0.8, -0.3)}
        stream_data = {"channel": f"stream_{random.randint(1000, 9999)}"}

        payload = {
            "report_id": report_id,
            "format": "graphical",
            "tail_risk_metrics": tail_risk,
            "stream_payload": stream_data
        }

        result = self.visualizer.visualize(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("tail_risk_metrics"), tail_risk)
        self.assertEqual(result.get("stream_payload"), stream_data)


if __name__ == "__main__":
    unittest.main()