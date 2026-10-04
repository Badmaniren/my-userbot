import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.adaptive_risk_score = round(random.uniform(1.0, 100.0), 2)
        self.visualizer_instance = MarketPortfolioStressAuditVisualizer(db_storage=None)

    def test_integration_text_summary_flow(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.adaptive_risk_score,
            "export_to_text_report": True
        }

        result_func = market_portfolio_stress_audit_visualizer(payload)
        result_class = self.visualizer_instance.visualize(payload)

        self.assertIn(self.portfolio_id, result_func)
        self.assertIn(str(self.adaptive_risk_score), result_func)
        self.assertIn("Exported to text report successfully.", result_func)

        self.assertEqual(result_func, result_class)

    def test_integration_graphical_flow_with_monte_carlo(self):
        mc_payload = {
            "portfolio_id": self.portfolio_id,
            "simulations": random.randint(100, 1000)
        }
        monte_carlo_result = market_portfolio_stress_monte_carlo_engine(mc_payload)

        payload = {
            "report_id": self.portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": self.adaptive_risk_score,
            "tail_risk_metrics": {"var_95": random.uniform(-0.5, -0.1)},
            "monte_carlo_simulation": monte_carlo_result
        }

        result = self.visualizer_instance.visualize(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), self.adaptive_risk_score)
        self.assertIn("tail_risk_metrics", result)
        self.assertEqual(result.get("monte_carlo_simulation"), monte_carlo_result)

    def test_integration_invalid_payload_handling(self):
        random_payload_string = str(uuid.uuid4())
        result = market_portfolio_stress_audit_visualizer(random_payload_string)
        self.assertEqual(result, random_payload_string)

if __name__ == "__main__":
    unittest.main()