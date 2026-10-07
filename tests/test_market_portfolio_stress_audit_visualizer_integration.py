import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer


class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def test_visualizer_integration_text_and_graphical_flows(self):
        portfolio_id = str(uuid.uuid4())
        adaptive_score = round(random.uniform(1.0, 99.9), 2)
        tail_metric = round(random.uniform(0.01, 0.99), 4)

        visualizer = MarketPortfolioStressAuditVisualizer(
            db_storage=None,
            market_portfolio_stress_scenario_matrix_evaluator=None,
            market_portfolio_stress_monte_carlo_engine=None
        )

        payload_text = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }

        result_text = visualizer.visualize(payload_text)
        
        self.assertIsInstance(result_text, str)
        self.assertIn(portfolio_id, result_text)
        self.assertIn(str(adaptive_score), result_text)
        self.assertIn("Exported to text report successfully", result_text)

        payload_graphical = {
            "report_id": portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": adaptive_score,
            "tail_risk_metrics": {"var_95": tail_metric},
            "stream_payload": {"status": "active"}
        }

        result_graphical = visualizer.visualize(payload_graphical)

        self.assertIsInstance(result_graphical, dict)
        self.assertEqual(result_graphical.get("portfolio_id"), portfolio_id)
        self.assertEqual(result_graphical.get("status"), "success")
        self.assertEqual(result_graphical.get("layout"), "graphical")
        self.assertEqual(result_graphical.get("adaptive_risk_score"), adaptive_score)
        self.assertEqual(result_graphical.get("tail_risk_metrics"), {"var_95": tail_metric})
        self.assertEqual(result_graphical.get("stream_payload"), {"status": "active"})


if __name__ == "__main__":
    unittest.main()