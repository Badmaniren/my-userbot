import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def test_visualizer_integration_flow(self):
        portfolio_id_val = str(uuid.uuid4())
        risk_metric_value = round(random.uniform(10.5, 99.9), 2)
        
        payload = {
            "portfolio_id": portfolio_id_val,
            "format": "text_summary",
            "adaptive_risk_score": risk_metric_value,
            "export_to_text_report": True
        }

        visualizer = MarketPortfolioStressAuditVisualizer(
            db_storage=None,
            market_portfolio_stress_monte_carlo_engine=None,
            market_report_generator=None
        )

        result = visualizer.visualize(payload)

        self.assertIsInstance(result, str)
        self.assertIn(portfolio_id_val, result)
        self.assertIn("Portfolio Stress Audit Summary", result)

        payload_graphical = {
            "report_id": portfolio_id_val,
            "format": "graphical",
            "adaptive_risk_score": risk_metric_value
        }

        result_graphical = visualizer.visualize(payload_graphical)

        self.assertIsInstance(result_graphical, dict)
        self.assertEqual(result_graphical.get("portfolio_id"), portfolio_id_val)
        self.assertEqual(result_graphical.get("status"), "success")
        self.assertEqual(result_graphical.get("layout"), "graphical")

if __name__ == "__main__":
    unittest.main()