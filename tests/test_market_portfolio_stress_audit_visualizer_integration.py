import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer


class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def test_visualizer_integration_flow(self):
        portfolio_id = f"PORT-{uuid.uuid4()}"
        adaptive_score = round(random.uniform(1.0, 99.9), 2)
        
        visualizer = MarketPortfolioStressAuditVisualizer(
            db_storage=None,
            market_portfolio_stress_scenario_pipeline=None,
            market_portfolio_audit_compliance_hub=None
        )

        payload_text = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }

        response_text = visualizer.visualize(payload_text)
        
        self.assertIsInstance(response_text, str)
        self.assertIn(portfolio_id, response_text)
        self.assertIn(str(adaptive_score), response_text)
        self.assertIn("Exported to text report successfully", response_text)

        payload_graph = {
            "report_id": portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": adaptive_score
        }

        response_graph = visualizer.visualize(payload_graph)

        self.assertIsInstance(response_graph, dict)
        self.assertEqual(response_graph.get("portfolio_id"), portfolio_id)
        self.assertEqual(response_graph.get("status"), "success")
        self.assertEqual(response_graph.get("layout"), "graphical")
        self.assertEqual(response_graph.get("adaptive_risk_score"), adaptive_score)


if __name__ == "__main__":
    unittest.main()