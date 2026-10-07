import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer, market_portfolio_stress_audit_visualizer

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def test_visualizer_integration_text_format(self):
        portfolio_id = str(uuid.uuid4())
        adaptive_score = round(random.uniform(1.0, 100.0), 2)
        
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }

        visualizer = MarketPortfolioStressAuditVisualizer(db_storage="real_db_mock")
        result = visualizer.visualize(payload)

        self.assertIsInstance(result, str)
        self.assertIn(portfolio_id, result)
        self.assertIn(str(adaptive_score), result)
        self.assertIn("Exported to text report successfully.", result)

    def test_visualizer_integration_graphical_format(self):
        report_id = f"rep-{uuid.uuid4()}"
        tail_risk = {"var_99": random.uniform(-0.5, -0.1), "cvar": random.uniform(-0.8, -0.2)}
        stream_data = {"status": "streaming", "node": random.randint(1, 10)}

        payload = {
            "report_id": report_id,
            "format": "graphical",
            "tail_risk_metrics": tail_risk,
            "stream_payload": stream_data
        }

        result = market_portfolio_stress_audit_visualizer(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("tail_risk_metrics"), tail_risk)
        self.assertEqual(result.get("stream_payload"), stream_data)

    def test_visualizer_non_dict_payload(self):
        random_string = str(uuid.uuid4())
        result = market_portfolio_stress_audit_visualizer(random_string)
        self.assertEqual(result, random_string)

if __name__ == "__main__":
    unittest.main()