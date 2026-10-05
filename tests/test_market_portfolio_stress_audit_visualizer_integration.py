import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer


class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.adaptive_risk_score = round(random.uniform(1.0, 100.0), 2)
        self.tail_risk_metrics = {"VaR_99": random.uniform(-0.15, -0.01), "ExpectedShortfall": random.uniform(-0.25, -0.05)}
        self.stream_payload = {"status_code": random.choice([200, 201, 202]), "nodes_active": random.randint(1, 10)}
        
        self.visualizer = MarketPortfolioStressAuditVisualizer(
            db_storage=None,
            market_portfolio_stress_scenario_matrix_evaluator=None,
            market_portfolio_stress_monte_carlo_engine=None
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
        self.assertIn("Exported to text report successfully.", result)

    def test_visualizer_graphical_layout_integration(self):
        payload = {
            "report_id": self.portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": self.adaptive_risk_score,
            "tail_risk_metrics": self.tail_risk_metrics,
            "stream_payload": self.stream_payload
        }
        result = self.visualizer.visualize(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), self.adaptive_risk_score)
        self.assertEqual(result.get("tail_risk_metrics"), self.tail_risk_metrics)
        self.assertEqual(result.get("stream_payload"), self.stream_payload)


if __name__ == "__main__":
    unittest.main()